import asyncio
import hashlib
import json
import logging
import math
import re
from typing import Any, Dict, List, Optional

try:
    import boto3
except ImportError:
    boto3 = None
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating high-dimensional vector embeddings across multiple providers (Bedrock, Gemini, OpenAI, Local)."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        bedrock_region: Optional[str] = None,
        bedrock_access_key_id: Optional[str] = None,
        bedrock_secret_access_key: Optional[str] = None,
        bedrock_session_token: Optional[str] = None,
    ):
        self.provider = (provider or getattr(settings, "EMBEDDING_PROVIDER", "gemini") or "gemini").lower()
        default_model = (
            getattr(settings, "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
            if self.provider in {"bedrock", "aws", "titan"}
            else getattr(settings, "EMBEDDING_MODEL", "text-embedding-004")
        )
        self.model = model or default_model
        self.gemini_key = gemini_api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.openai_key = openai_api_key or getattr(settings, "OPENAI_API_KEY", None)
        self.bedrock_region = bedrock_region or getattr(settings, "BEDROCK_AWS_REGION", "us-east-1")
        self.bedrock_access_key_id = (
            bedrock_access_key_id
            or getattr(settings, "BEDROCK_AWS_ACCESS_KEY_ID", None)
            or getattr(settings, "AWS_ACCESS_KEY_ID", None)
            or getattr(settings, "S3_ACCESS_KEY", None)
        )
        self.bedrock_secret_access_key = (
            bedrock_secret_access_key
            or getattr(settings, "BEDROCK_AWS_SECRET_ACCESS_KEY", None)
            or getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
            or getattr(settings, "S3_SECRET_KEY", None)
        )
        self.bedrock_session_token = (
            bedrock_session_token
            or getattr(settings, "BEDROCK_AWS_SESSION_TOKEN", None)
            or getattr(settings, "AWS_SESSION_TOKEN", None)
        )
        self._bedrock_client = None

    def _get_bedrock_client(self):
        if self._bedrock_client is not None:
            return self._bedrock_client
        if boto3 is None:
            raise RuntimeError("boto3 is required for Amazon Bedrock integration. Please install boto3.")
        kwargs = {"region_name": self.bedrock_region}
        if self.bedrock_access_key_id and self.bedrock_secret_access_key:
            kwargs["aws_access_key_id"] = self.bedrock_access_key_id
            kwargs["aws_secret_access_key"] = self.bedrock_secret_access_key
            if self.bedrock_session_token:
                kwargs["aws_session_token"] = self.bedrock_session_token
        self._bedrock_client = boto3.client("bedrock-runtime", **kwargs)
        return self._bedrock_client

    async def get_embedding(self, text: str) -> List[float]:
        """Generate a vector embedding for a single text."""
        if not text or not text.strip():
            return [0.0] * 64

        text = text.strip()

        if self.provider in {"local", "mock", "none"}:
            return self._embed_local(text)

        # 1. Try Amazon Bedrock if configured
        if self.provider in {"bedrock", "aws", "titan"}:
            try:
                emb = await self._embed_bedrock(text)
                if emb:
                    return emb
            except Exception as e:
                logger.warning("Bedrock embedding error: %s. Falling back to next provider or local vectorizer.", e)

        # 2. Try Gemini if configured
        if self.provider == "gemini" and self.gemini_key:
            try:
                emb = await self._embed_gemini(text)
                if emb:
                    return emb
            except Exception as e:
                logger.warning("Gemini embedding API error: %s. Falling back to local vectorizer.", e)

        # 3. Try OpenAI if configured
        if self.provider == "openai" and self.openai_key:
            try:
                emb = await self._embed_openai(text)
                if emb:
                    return emb
            except Exception as e:
                logger.warning("OpenAI embedding API error: %s. Falling back to local vectorizer.", e)

        # Resilient local deterministic vectorizer fallback
        return self._embed_local(text)

    async def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts."""
        if not texts:
            return []

        valid_texts = [t.strip() for t in texts if t and t.strip()]
        if not valid_texts:
            return [[0.0] * 64] * len(texts)

        if self.provider in {"local", "mock", "none"}:
            return [self._embed_local(t) for t in valid_texts]

        # 1. Try Amazon Bedrock batch
        if self.provider in {"bedrock", "aws", "titan"}:
            try:
                emb_batch = await self._embed_bedrock_batch(valid_texts)
                if emb_batch and len(emb_batch) == len(valid_texts):
                    return emb_batch
            except Exception as e:
                logger.warning("Bedrock batch embedding failed: %s. Falling back to individual/local.", e)

        # 2. Try Gemini batch
        if self.provider == "gemini" and self.gemini_key:
            try:
                emb_batch = await self._embed_gemini_batch(valid_texts)
                if emb_batch and len(emb_batch) == len(valid_texts):
                    return emb_batch
            except Exception as e:
                logger.warning("Gemini batch embedding failed: %s. Falling back to individual/local.", e)

        # 3. Try OpenAI batch
        if self.provider == "openai" and self.openai_key:
            try:
                emb_batch = await self._embed_openai_batch(valid_texts)
                if emb_batch and len(emb_batch) == len(valid_texts):
                    return emb_batch
            except Exception as e:
                logger.warning("OpenAI batch embedding failed: %s. Falling back to individual/local.", e)

        results = []
        for t in valid_texts:
            results.append(await self.get_embedding(t))
        return results

    # --------------------------------------------------------------------------
    # Amazon Bedrock Embeddings (Titan Text Embeddings V2/V1, Cohere Embed)
    # --------------------------------------------------------------------------
    async def _embed_bedrock(self, text: str) -> Optional[List[float]]:
        def _invoke():
            client = self._get_bedrock_client()
            model_id = self.model or getattr(settings, "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
            if "cohere" in model_id.lower():
                body = json.dumps({
                    "texts": [text],
                    "input_type": "search_document",
                    "truncate": "RIGHT",
                })
            else:
                body = json.dumps({
                    "inputText": text,
                    "dimensions": 1024 if "v2" in model_id else 1536,
                    "normalize": True,
                })
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            raw_body = response.get("body")
            content = raw_body.read() if hasattr(raw_body, "read") else raw_body
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            data = json.loads(content) if isinstance(content, str) else content

            if isinstance(data, dict):
                if "embedding" in data:
                    return data["embedding"]
                elif "embeddings" in data and isinstance(data["embeddings"], list) and data["embeddings"]:
                    return data["embeddings"][0]
            return None

        return await asyncio.to_thread(_invoke)

    async def _embed_bedrock_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        model_id = self.model or getattr(settings, "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
        if "cohere" in model_id.lower():
            def _invoke_cohere():
                client = self._get_bedrock_client()
                body = json.dumps({
                    "texts": texts,
                    "input_type": "search_document",
                    "truncate": "RIGHT",
                })
                response = client.invoke_model(
                    modelId=model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=body,
                )
                raw_body = response.get("body")
                content = raw_body.read() if hasattr(raw_body, "read") else raw_body
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                data = json.loads(content) if isinstance(content, str) else content
                return data.get("embeddings") if isinstance(data, dict) else None

            return await asyncio.to_thread(_invoke_cohere)
        else:
            results = await asyncio.gather(*[self._embed_bedrock(t) for t in texts], return_exceptions=True)
            valid = []
            for r in results:
                if isinstance(r, list) and r:
                    valid.append(r)
                else:
                    return None
            return valid

    # --------------------------------------------------------------------------
    # Google Gemini Embeddings
    # --------------------------------------------------------------------------
    async def _embed_gemini(self, text: str) -> Optional[List[float]]:
        model_name = self.model if "embedding" in self.model else "text-embedding-004"
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:embedContent?key={self.gemini_key}"
        payload = {
            "model": model_name,
            "content": {
                "parts": [{"text": text}]
            }
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                values = data.get("embedding", {}).get("values")
                if values and isinstance(values, list):
                    return values
            else:
                logger.warning("Gemini embedContent returned status %s: %s", resp.status_code, resp.text)
        return None

    async def _embed_gemini_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        model_name = self.model if "embedding" in self.model else "text-embedding-004"
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:batchEmbedContents?key={self.gemini_key}"
        requests = [
            {"model": model_name, "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        payload = {"requests": requests}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                embeddings = data.get("embeddings", [])
                if len(embeddings) == len(texts):
                    return [item.get("values", []) for item in embeddings]
            else:
                logger.warning("Gemini batchEmbedContents status %s: %s", resp.status_code, resp.text)
        return None

    # --------------------------------------------------------------------------
    # OpenAI Embeddings
    # --------------------------------------------------------------------------
    async def _embed_openai(self, text: str) -> Optional[List[float]]:
        model_name = self.model if "embedding" in self.model else "text-embedding-3-small"
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model_name, "input": text}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                emb_list = data.get("data", [])
                if emb_list:
                    return emb_list[0].get("embedding")
            else:
                logger.warning("OpenAI embed returned status %s: %s", resp.status_code, resp.text)
        return None

    async def _embed_openai_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        model_name = self.model if "embedding" in self.model else "text-embedding-3-small"
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": model_name, "input": texts}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                emb_list = data.get("data", [])
                if len(emb_list) == len(texts):
                    sorted_items = sorted(emb_list, key=lambda x: x.get("index", 0))
                    return [item.get("embedding", []) for item in sorted_items]
            else:
                logger.warning("OpenAI batch embed returned status %s: %s", resp.status_code, resp.text)
        return None

    # --------------------------------------------------------------------------
    # Resilient Local Semantic Vectorizer (Hash + N-gram with Cosine Normalization)
    # --------------------------------------------------------------------------
    def _embed_local(self, text: str, dimension: int = 256) -> List[float]:
        """Fast, zero-dependency semantic hash embedding with L2-normalization."""
        vector = [0.0] * dimension
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vector

        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % dimension
            vector[h] += 1.0

            for i in range(len(word) - 1):
                bg = word[i:i+2]
                h_bg = int(hashlib.md5(bg.encode("utf-8")).hexdigest(), 16) % dimension
                vector[h_bg] += 0.3

        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0.0:
            return [x / norm for x in vector]
        return vector

