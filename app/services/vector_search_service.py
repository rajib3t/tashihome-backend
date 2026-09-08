from __future__ import annotations
import asyncio
import logging
import math
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorSearchService:
    """High-performance vector and hybrid semantic search engine for TashiHome homestays."""

    _instance: Optional["VectorSearchService"] = None

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        storage_service: Optional[Any] = None,
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self._storage_service = storage_service
        # In-memory vector index: property_id -> {vector, metadata, doc_text}
        self._index: Dict[int, Dict[str, Any]] = {}
        self._last_synced_at: Optional[datetime] = None
        self._sync_lock = asyncio.Lock()

    @classmethod
    def get_instance(
        cls,
        embedding_service: Optional[EmbeddingService] = None,
        storage_service: Optional[Any] = None,
    ) -> "VectorSearchService":
        if cls._instance is None:
            cls._instance = cls(
                embedding_service=embedding_service,
                storage_service=storage_service,
            )
        else:
            if embedding_service is not None:
                cls._instance.embedding_service = embedding_service
            if storage_service is not None:
                cls._instance._storage_service = storage_service
        return cls._instance

    def _get_storage_service(self) -> Optional[Any]:
        if self._storage_service is not None:
            return self._storage_service
        try:
            from app.services.storage_service import StorageService
            self._storage_service = StorageService()
            return self._storage_service
        except Exception as e:
            logger.warning("Could not initialize StorageService for vector persistence: %s", e)
            return None

    def _get_s3_bucket(self, override_bucket: Optional[str] = None) -> str:
        return (
            override_bucket
            or getattr(settings, "VECTOR_S3_BUCKET", None)
            or getattr(settings, "S3_VECTOR_BUCKET", None)
            or getattr(settings, "S3_BUCKET", None)
            or "tashihome-vector"
        )

    def _get_s3_key(self, override_key: Optional[str] = None) -> str:
        return (
            override_key
            or getattr(settings, "VECTOR_S3_KEY", None)
            or "vectors/homestays_vector_index.json"
        )

    # --------------------------------------------------------------------------
    # Cosine Similarity Calculation
    # --------------------------------------------------------------------------
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vector lists."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for a, b in zip(vec_a, vec_b):
            dot += a * b
            norm_a += a * a
            norm_b += b * b

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        sim = dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
        return max(0.0, min(1.0, float(sim)))

    # --------------------------------------------------------------------------
    # Document Chunk Builder
    # --------------------------------------------------------------------------
    def build_homestay_document(self, prop: Any) -> str:
        """Construct a dense, rich semantic text document representing the homestay."""
        name = getattr(prop, "name", "") or ""
        prop_type = getattr(prop, "type", "homestay") or "homestay"
        if hasattr(prop_type, "value"):
            prop_type = prop_type.value
        elif not isinstance(prop_type, str):
            prop_type = str(prop_type)

        description = getattr(prop, "description", "") or ""
        address = getattr(prop, "address", "") or ""
        price = float(getattr(prop, "price_per_night", 0) or 0)
        currency = getattr(prop, "currency", "INR") or "INR"

        # City / Region
        city_name = ""
        city_obj = getattr(prop, "city", None)
        if city_obj:
            city_name = getattr(city_obj, "name", "") or ""

        location_name = ""
        loc_obj = getattr(prop, "location", None)
        if loc_obj:
            location_name = getattr(loc_obj, "name", "") or ""

        # Extract amenities / room features if present
        features = []
        if hasattr(prop, "property_amenities") and prop.property_amenities:
            for pa in prop.property_amenities:
                amenity = getattr(pa, "amenity", None)
                if amenity and getattr(amenity, "name", None):
                    features.append(amenity.name)
        elif hasattr(prop, "amenities") and prop.amenities:
            for a in prop.amenities:
                if isinstance(a, str):
                    features.append(a)
                elif hasattr(a, "name"):
                    features.append(a.name)

        if hasattr(prop, "property_facilities") and prop.property_facilities:
            for pf in prop.property_facilities:
                fac = getattr(pf, "facility", None)
                if fac and getattr(fac, "name", None):
                    features.append(fac.name)

        # Country / Region
        country_name = ""
        country_obj = getattr(prop, "country", None) or (getattr(city_obj, "country", None) if city_obj else None)
        if country_obj:
            country_name = getattr(country_obj, "name", "") or ""

        features_str = ", ".join(features) if features else "Authentic local hospitality"

        loc_parts = [p for p in [city_name, location_name, address, country_name] if p]
        location_str = " ".join(loc_parts)

        doc = (
            f"Homestay Name: {name}. "
            f"Property Type: {prop_type}. "
            f"Location: {location_str}. "
            f"Price: {currency} {price:.2f} per night. "
            f"Atmosphere and Description: {description}. "
            f"Amenities, Experiences & Highlights: {features_str}."
        )
        return doc.strip()

    # --------------------------------------------------------------------------
    # S3 Vector Persistence (tashihome-vector bucket)
    # --------------------------------------------------------------------------
    async def save_to_s3(
        self,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Serialize in-memory vector embeddings index and upload to S3 vector bucket (e.g. tashihome-vector)."""
        target_bucket = self._get_s3_bucket(bucket)
        target_key = self._get_s3_key(key)

        payload = {
            "version": "1.0",
            "provider": getattr(self.embedding_service, "provider", "bedrock"),
            "model": getattr(self.embedding_service, "model", "amazon.titan-embed-text-v2:0"),
            "total_properties": len(self._index),
            "last_synced_at": (self._last_synced_at or datetime.utcnow()).isoformat(),
            "index": {
                str(prop_id): {
                    "vector": item.get("vector", []),
                    "metadata": item.get("metadata", {}),
                    "document": item.get("document", ""),
                    "updated_at": item.get("updated_at", datetime.utcnow()).isoformat()
                    if isinstance(item.get("updated_at"), datetime)
                    else str(item.get("updated_at", "")),
                }
                for prop_id, item in self._index.items()
            },
        }

        try:
            storage = self._get_storage_service()
            if storage:
                await storage.upload_json(key=target_key, data=payload, bucket=target_bucket)
                logger.info(
                    "Successfully saved %d vector embeddings to S3 bucket '%s' key '%s'",
                    len(self._index),
                    target_bucket,
                    target_key,
                )
                return {
                    "success": True,
                    "persisted": True,
                    "bucket": target_bucket,
                    "key": target_key,
                    "total_saved": len(self._index),
                }
        except Exception as e:
            logger.warning("Failed to save vector embeddings to S3 (%s/%s): %s", target_bucket, target_key, e)

        return {
            "success": False,
            "persisted": False,
            "bucket": target_bucket,
            "key": target_key,
            "total_saved": len(self._index),
        }

    async def load_from_s3(
        self,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
    ) -> int:
        """Load precomputed vector embeddings index from S3 vector bucket."""
        target_bucket = self._get_s3_bucket(bucket)
        target_key = self._get_s3_key(key)

        try:
            storage = self._get_storage_service()
            if storage:
                data = await storage.get_object_json(key=target_key, bucket=target_bucket)
                if data and isinstance(data, dict) and "index" in data:
                    loaded_index = {}
                    for k, item in data["index"].items():
                        try:
                            prop_id = int(k)
                            loaded_index[prop_id] = {
                                "vector": item.get("vector", []),
                                "metadata": item.get("metadata", {}),
                                "document": item.get("document", ""),
                                "updated_at": datetime.fromisoformat(item["updated_at"])
                                if "updated_at" in item and isinstance(item["updated_at"], str)
                                else datetime.utcnow(),
                            }
                        except Exception:
                            continue

                    self._index.update(loaded_index)
                    if "last_synced_at" in data and data["last_synced_at"]:
                        try:
                            self._last_synced_at = datetime.fromisoformat(data["last_synced_at"])
                        except Exception:
                            self._last_synced_at = datetime.utcnow()
                    else:
                        self._last_synced_at = datetime.utcnow()

                    logger.info(
                        "Loaded %d vector embeddings from S3 bucket '%s' key '%s'",
                        len(loaded_index),
                        target_bucket,
                        target_key,
                    )
                    return len(loaded_index)
        except Exception as e:
            logger.warning("Failed to load vector embeddings from S3 (%s/%s): %s", target_bucket, target_key, e)

        return 0

    # --------------------------------------------------------------------------
    # Index Management
    # --------------------------------------------------------------------------
    async def index_property(
        self,
        prop: Any,
        persist_s3: Optional[bool] = None,
    ) -> None:
        """Embed and index a single property."""
        prop_id = getattr(prop, "id", None)
        if not prop_id:
            return

        doc_text = self.build_homestay_document(prop)
        vector = await self.embedding_service.get_embedding(doc_text)

        city_obj = getattr(prop, "city", None)
        city_name = getattr(city_obj, "name", "") if city_obj else ""

        prop_type = getattr(prop, "type", "")
        if hasattr(prop_type, "value"):
            prop_type = prop_type.value
        elif not isinstance(prop_type, str):
            prop_type = str(prop_type)

        metadata = {
            "id": prop_id,
            "public_id": str(getattr(prop, "public_id", "")),
            "name": getattr(prop, "name", ""),
            "slug": getattr(prop, "slug", ""),
            "city_name": city_name,
            "address": getattr(prop, "address", ""),
            "price_per_night": float(getattr(prop, "price_per_night", 0) or 0),
            "type": prop_type,
            "is_featured": bool(getattr(prop, "is_featured", False)),
        }

        self._index[prop_id] = {
            "vector": vector,
            "metadata": metadata,
            "document": doc_text,
            "updated_at": datetime.utcnow(),
        }

        should_persist = persist_s3 if persist_s3 is not None else getattr(settings, "VECTOR_PERSIST_S3", True)
        if should_persist:
            await self.save_to_s3()

    async def index_properties(
        self,
        properties: List[Any],
        persist_s3: Optional[bool] = None,
    ) -> int:
        """Batch index multiple properties."""
        if not properties:
            return 0

        docs = []
        valid_props = []
        for p in properties:
            p_id = getattr(p, "id", None)
            if p_id:
                docs.append(self.build_homestay_document(p))
                valid_props.append(p)

        if not docs:
            return 0

        vectors = await self.embedding_service.get_batch_embeddings(docs)

        for prop, doc_text, vector in zip(valid_props, docs, vectors):
            prop_id = prop.id
            city_obj = getattr(prop, "city", None)
            city_name = getattr(city_obj, "name", "") if city_obj else ""

            prop_type = getattr(prop, "type", "")
            if hasattr(prop_type, "value"):
                prop_type = prop_type.value
            elif not isinstance(prop_type, str):
                prop_type = str(prop_type)

            metadata = {
                "id": prop_id,
                "public_id": str(getattr(prop, "public_id", "")),
                "name": getattr(prop, "name", ""),
                "slug": getattr(prop, "slug", ""),
                "city_name": city_name,
                "address": getattr(prop, "address", ""),
                "price_per_night": float(getattr(prop, "price_per_night", 0) or 0),
                "type": prop_type,
                "is_featured": bool(getattr(prop, "is_featured", False)),
            }

            self._index[prop_id] = {
                "vector": vector,
                "metadata": metadata,
                "document": doc_text,
                "updated_at": datetime.utcnow(),
            }

        self._last_synced_at = datetime.utcnow()
        logger.info("Indexed %d properties for vector search.", len(valid_props))

        should_persist = persist_s3 if persist_s3 is not None else getattr(settings, "VECTOR_PERSIST_S3", True)
        if should_persist and len(valid_props) > 0:
            await self.save_to_s3()

        return len(valid_props)

    # --------------------------------------------------------------------------
    # Semantic Search Engine
    # --------------------------------------------------------------------------
    async def search(
        self,
        query: str,
        city_name: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        property_type: Optional[str] = None,
        limit: int = 8,
        min_similarity: Optional[float] = None,
        auto_load_s3: bool = True,
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector similarity search with business constraint filters."""
        if not query or not query.strip():
            return []

        # If index is empty, attempt to load pre-computed vectors from S3
        if len(self._index) == 0 and auto_load_s3:
            await self.load_from_s3()

        threshold = (
            min_similarity
            if min_similarity is not None
            else getattr(settings, "VECTOR_SIMILARITY_THRESHOLD", 0.25)
        )
        limit = limit or getattr(settings, "VECTOR_TOP_K", 8)

        # 1. Embed user query
        query_vector = await self.embedding_service.get_embedding(query)
        if not query_vector:
            return []

        # 2. Score candidates in index
        scored_candidates: List[Tuple[float, Dict[str, Any]]] = []

        for prop_id, item in self._index.items():
            meta = item.get("metadata", {})
            vector = item.get("vector", [])

            # Hard Constraint Filters
            if city_name:
                item_city = (meta.get("city_name") or "").lower()
                if city_name.lower() not in item_city:
                    continue

            price = meta.get("price_per_night", 0.0)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue

            if property_type:
                item_type = (meta.get("type") or "").lower()
                if property_type.lower() != item_type:
                    continue

            # Compute Cosine Similarity
            similarity = self.cosine_similarity(query_vector, vector)

            if similarity >= threshold:
                scored_candidates.append((similarity, meta))

        # 3. Sort descending by similarity
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # 4. Format top results
        results = []
        for score, meta in scored_candidates[:limit]:
            results.append({
                "id": str(meta.get("public_id") or meta.get("id")),
                "name": meta.get("name"),
                "slug": meta.get("slug"),
                "city_name": meta.get("city_name"),
                "price_per_night": meta.get("price_per_night"),
                "type": meta.get("type"),
                "similarity_score": round(score, 4),
                "match_percentage": round(score * 100, 1),
            })

        return results

    @property
    def total_indexed(self) -> int:
        return len(self._index)

    @property
    def last_synced_at(self) -> Optional[datetime]:
        return self._last_synced_at

