#!/usr/bin/env python3
"""
TashiHome Homestay Vector Embedding Synchronization CLI.
Pre-computes and indexes rich vector embeddings for all active homestays.

Usage:
    python scripts/sync_embeddings.py
    python scripts/sync_embeddings.py --provider gemini --model text-embedding-004
"""

import argparse
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.repositories.property_repository import PropertyRepository
from app.services.embedding_service import EmbeddingService
from app.services.property_service import PropertyService
from app.services.vector_search_service import VectorSearchService


async def main(provider: str, model: str, force: bool, bucket: str = None, save_s3: bool = True, load_s3: bool = False):
    print(f"🚀 Initializing TashiHome Vector Embedding Indexer...")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    print(f"   S3 Vector Bucket: {bucket or settings.VECTOR_S3_BUCKET or 'tashihome-vector'}")
    print(f"   S3 Vector Key: {settings.VECTOR_S3_KEY}")
    print(f"   Environment: {settings.ENV}")

    embedding_svc = EmbeddingService(
        provider=provider,
        model=model,
        gemini_api_key=settings.GEMINI_API_KEY,
        openai_api_key=settings.OPENAI_API_KEY,
    )
    vector_svc = VectorSearchService.get_instance(embedding_service=embedding_svc)

    if load_s3:
        print(f"📥 Loading existing vector index from S3...")
        loaded = await vector_svc.load_from_s3(bucket=bucket)
        print(f"   Loaded {loaded} properties from S3.")
        if not force and loaded > 0:
            print(f"🎉 Vector index successfully loaded from S3! Total indexed: {vector_svc.total_indexed}")
            return

    async with AsyncSessionLocal() as session:
        prop_repo = PropertyRepository(session)
        prop_svc = PropertyService(prop_repo)

        print(f"📦 Fetching active properties from database...")
        page_result = await prop_svc.get_all(
            is_active=True,
            page=1,
            page_size=500,
            with_relations={
                "city": True,
                "location": True,
                "property_assets": True,
                "property_amenities": True,
                "property_facilities": True,
            },
        )
        items = getattr(page_result, "items", page_result) or []
        print(f"   Found {len(items)} active property record(s).")

        if not items:
            print("⚠️ No active properties found in database.")
            return

        print(f"⚙️ Generating embeddings and indexing...")
        indexed = await vector_svc.index_properties(items, persist_s3=save_s3)
        print(f"✅ Successfully indexed {indexed} homestays into vector store.")

        if save_s3:
            s3_res = await vector_svc.save_to_s3(bucket=bucket)
            if s3_res.get("persisted"):
                print(f"☁️ Saved vector embeddings index to S3 bucket '{s3_res.get('bucket')}' key '{s3_res.get('key')}'.")
            else:
                print(f"⚠️ S3 save skipped or not configured for bucket '{s3_res.get('bucket')}'.")

        # Test search query
        print("\n🔍 Running sample semantic test search: 'cozy traditional cottage with mountain view'...")
        results = await vector_svc.search("cozy traditional cottage with mountain view", limit=3)
        print(f"   Matched {len(results)} properties:")
        for r in results:
            print(f"   - {r['name']} ({r.get('city_name')}) -> Similarity: {r['similarity_score']} ({r['match_percentage']}%)")

    print("\n🎉 Done! Vector index is ready.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TashiHome Vector Embedding Sync CLI")
    parser.add_argument("--provider", default=settings.EMBEDDING_PROVIDER or "bedrock", help="Embedding provider: bedrock | gemini | openai | local")
    parser.add_argument("--model", default=settings.EMBEDDING_MODEL or "amazon.titan-embed-text-v2:0", help="Embedding model name")
    parser.add_argument("--bucket", default=settings.VECTOR_S3_BUCKET or "tashihome-vector", help="S3 vector storage bucket name")
    parser.add_argument("--force", action="store_true", help="Force re-indexing from DB")
    parser.add_argument("--load-s3", action="store_true", help="Load existing vector index from S3 first")
    parser.add_argument("--no-save-s3", action="store_true", help="Do not save vectors to S3")
    args = parser.parse_args()

    asyncio.run(main(
        provider=args.provider,
        model=args.model,
        force=args.force,
        bucket=args.bucket,
        save_s3=not args.no_save_s3,
        load_s3=args.load_s3,
    ))

