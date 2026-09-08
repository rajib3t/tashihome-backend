import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.models.property_model import PropertyStatus, PropertyType
from app.mcp.tools import MCPToolExecutor
from app.services.assistant_service import AssistantService
from app.services.embedding_service import EmbeddingService
from app.services.vector_search_service import VectorSearchService


class DummyCity:
    def __init__(self, id: int, name: str, slug: str):
        self.id = id
        self.name = name
        self.slug = slug


class DummyAmenity:
    def __init__(self, name: str):
        self.name = name


class DummyPropertyAmenity:
    def __init__(self, name: str):
        self.amenity = DummyAmenity(name)


class DummyProperty:
    def __init__(
        self,
        id: int,
        name: str,
        slug: str,
        description: str,
        city_name: str,
        price: float,
        prop_type: str = "home_stay",
        amenities: list = None,
    ):
        self.id = id
        self.public_id = uuid4()
        self.name = name
        self.slug = slug
        self.description = description
        self.city = DummyCity(1, city_name, city_name.lower())
        self.location = None
        self.address = f"Main Road, {city_name}"
        self.price_per_night = price
        self.sale_per_night = price
        self.currency = "BTN"
        self.type = prop_type
        self.status = PropertyStatus.ACTIVE
        self.is_featured = True
        self.property_assets = []
        self.property_amenities = [DummyPropertyAmenity(a) for a in (amenities or [])]


def test_embedding_service_local_fallback():
    async def run():
        service = EmbeddingService(provider="local")
        vector = await service.get_embedding("peaceful wooden homestay near monastery")
        assert isinstance(vector, list)
        assert len(vector) == 256
        assert any(x > 0 for x in vector)

        batch = await service.get_batch_embeddings([
            "stay with mountain view",
            "farm stay with organic food",
        ])
        assert len(batch) == 2
        assert len(batch[0]) == 256
        assert len(batch[1]) == 256

    asyncio.run(run())


def test_vector_search_service_similarity_and_ranking():
    async def run():
        emb_svc = EmbeddingService(provider="local")
        vector_svc = VectorSearchService(embedding_service=emb_svc)

        p1 = DummyProperty(
            id=1,
            name="Paro Pine Wood Sanctuary",
            slug="paro-pine-wood",
            description="A traditional wooden cottage in Paro valley with heated bukhari fireplace and majestic Himalayan mountain views.",
            city_name="Paro",
            price=3500.0,
            amenities=["Bukhari Fireplace", "Mountain View", "Wooden Bath"],
        )
        p2 = DummyProperty(
            id=2,
            name="Thimphu Urban Central Suite",
            slug="thimphu-urban-suite",
            description="Modern studio apartment in central Thimphu near shopping malls and business district with high speed fiber internet.",
            city_name="Thimphu",
            price=5000.0,
            amenities=["High Speed WiFi", "Workstation", "Elevator"],
        )
        p3 = DummyProperty(
            id=3,
            name="Bumthang Heritage Farm Retreat",
            slug="bumthang-farm-retreat",
            description="Authentic farm stay in Bumthang valley offering organic buckwheat meals and traditional hot stone bath.",
            city_name="Bumthang",
            price=2800.0,
            amenities=["Hot Stone Bath", "Organic Farm Meals", "Garden"],
        )

        indexed_count = await vector_svc.index_properties([p1, p2, p3])
        assert indexed_count == 3
        assert vector_svc.total_indexed == 3

        # Query 1: Search for fireplace / wooden mountain stay
        res1 = await vector_svc.search(
            query="wooden cottage with fireplace and mountain view",
            limit=3,
            min_similarity=0.0,
        )
        assert len(res1) > 0
        # Paro Pine Wood Sanctuary should rank first
        assert res1[0]["id"] == str(p1.public_id)
        assert res1[0]["slug"] == "paro-pine-wood"

        # Query 2: Search with city filter (Thimphu)
        res2 = await vector_svc.search(
            query="high speed internet for remote work",
            city_name="Thimphu",
            limit=3,
            min_similarity=0.0,
        )
        assert len(res2) == 1
        assert res2[0]["id"] == str(p2.public_id)

        # Query 3: Search with price filter
        res3 = await vector_svc.search(
            query="farm stay with hot stone bath",
            max_price=3000.0,
            limit=3,
            min_similarity=0.0,
        )
        assert len(res3) >= 1
        assert res3[0]["id"] == str(p3.public_id)

    asyncio.run(run())


def test_semantic_search_mcp_tool_execution():
    async def run():
        emb_svc = EmbeddingService(provider="local")
        vector_svc = VectorSearchService(embedding_service=emb_svc)

        p1 = DummyProperty(
            id=10,
            name="Himalayan Valley Homestay",
            slug="himalayan-valley-homestay",
            description="Charming riverside homestay with mountain views and home-cooked Bhutanese meals.",
            city_name="Punakha",
            price=3200.0,
            amenities=["Mountain View", "Riverside", "Bhutanese Meals"],
        )
        await vector_svc.index_properties([p1])

        tool_executor = MCPToolExecutor(
            property_service=MagicMock(),
            booking_service=MagicMock(),
            user_service=MagicMock(),
            vector_search_service=vector_svc,
        )

        result = await tool_executor.execute_tool(
            tool_name="semantic_search_homestays",
            arguments={"query": "riverside stay with mountain view", "city_name": "Punakha"},
        )

        assert not result.isError
        assert result.data is not None
        assert result.data["total"] >= 1
        assert result.data["properties"][0]["slug"] == "himalayan-valley-homestay"

    asyncio.run(run())


def test_assistant_chat_with_semantic_intent():
    async def run():
        emb_svc = EmbeddingService(provider="local")
        vector_svc = VectorSearchService(embedding_service=emb_svc)

        p1 = DummyProperty(
            id=20,
            name="Serene Apple Orchard Homestay",
            slug="serene-apple-orchard",
            description="Peaceful wooden cottage nestled among apple orchards with stunning mountain views and traditional hot stone bath.",
            city_name="Paro",
            price=4000.0,
            amenities=["Hot Stone Bath", "Apple Orchard", "Mountain View"],
        )
        await vector_svc.index_properties([p1])

        tool_executor = MCPToolExecutor(
            property_service=MagicMock(),
            booking_service=MagicMock(),
            user_service=MagicMock(),
            vector_search_service=vector_svc,
        )
        assistant_service = AssistantService(tool_executor=tool_executor)

        chat_resp = await assistant_service.chat(
            message="Find me a peaceful wooden cottage with mountain view and hot stone bath in Paro",
        )

        assert chat_resp.intent == "semantic_search_homestays"
        assert chat_resp.search_results is not None
        assert len(chat_resp.search_results) >= 1
        assert "Serene Apple Orchard" in chat_resp.reply

    asyncio.run(run())


def test_vector_save_to_s3_and_load_from_s3():
    async def run():
        emb_svc = EmbeddingService(provider="local")
        mock_storage = AsyncMock()
        uploaded_payload = {}

        async def fake_upload_json(key, data, bucket=None, cache_control=None):
            uploaded_payload[f"{bucket}/{key}"] = data
            return key

        async def fake_get_object_json(key, bucket=None):
            return uploaded_payload.get(f"{bucket}/{key}")

        mock_storage.upload_json = AsyncMock(side_effect=fake_upload_json)
        mock_storage.get_object_json = AsyncMock(side_effect=fake_get_object_json)

        vector_svc = VectorSearchService(
            embedding_service=emb_svc,
            storage_service=mock_storage,
        )

        p1 = DummyProperty(
            id=101,
            name="Tashi Dzong Mountain View Retreat",
            slug="tashi-dzong-mountain-view",
            description="Spectacular mountain view retreat near historic dzong in Punakha.",
            city_name="Punakha",
            price=4500.0,
            amenities=["Dzong View", "Mountain View", "Traditional Food"],
        )

        # 1. Index property (with S3 persistence)
        await vector_svc.index_properties([p1], persist_s3=True)

        assert mock_storage.upload_json.called
        call_kwargs = mock_storage.upload_json.call_args.kwargs
        assert call_kwargs.get("bucket") == "tashihome-vector"
        assert call_kwargs.get("key") == "vectors/homestays_vector_index.json"

        # Explicit save_to_s3
        res = await vector_svc.save_to_s3(bucket="tashihome-vector")
        assert res["success"] is True
        assert res["persisted"] is True
        assert res["bucket"] == "tashihome-vector"
        assert res["total_saved"] == 1

        # 2. Fresh service loading from S3
        fresh_svc = VectorSearchService(
            embedding_service=emb_svc,
            storage_service=mock_storage,
        )
        assert fresh_svc.total_indexed == 0

        loaded_count = await fresh_svc.load_from_s3(bucket="tashihome-vector")
        assert loaded_count == 1
        assert fresh_svc.total_indexed == 1
        assert 101 in fresh_svc._index
        assert fresh_svc._index[101]["metadata"]["name"] == "Tashi Dzong Mountain View Retreat"

        # 3. Perform semantic search on restored index
        search_results = await fresh_svc.search("historic dzong view retreat", limit=2)
        assert len(search_results) == 1
        assert search_results[0]["slug"] == "tashi-dzong-mountain-view"

    asyncio.run(run())


def test_vector_auto_load_from_s3_on_empty_search():
    async def run():
        emb_svc = EmbeddingService(provider="local")
        mock_storage = AsyncMock()

        cached_s3_data = {
            "version": "1.0",
            "provider": "bedrock",
            "model": "amazon.titan-embed-text-v2:0",
            "total_properties": 1,
            "last_synced_at": "2026-09-09T02:00:00",
            "index": {
                "202": {
                    "vector": [0.1] * 256,
                    "metadata": {
                        "id": 202,
                        "public_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "name": "Paro Valley Riverside Pine Chalet",
                        "slug": "paro-valley-riverside-pine-chalet",
                        "city_name": "Paro",
                        "price_per_night": 3800.0,
                        "type": "chalet",
                    },
                    "document": "Paro Valley Riverside Pine Chalet in Paro with river views",
                    "updated_at": "2026-09-09T02:00:00",
                }
            },
        }
        mock_storage.get_object_json = AsyncMock(return_value=cached_s3_data)

        # Empty vector service instance
        vector_svc = VectorSearchService(
            embedding_service=emb_svc,
            storage_service=mock_storage,
        )
        assert vector_svc.total_indexed == 0

        # Searching on empty index automatically loads from S3
        results = await vector_svc.search(
            query="riverside pine chalet",
            city_name="Paro",
            auto_load_s3=True,
            min_similarity=0.0,
        )
        assert vector_svc.total_indexed == 1
        assert len(results) == 1
        assert results[0]["slug"] == "paro-valley-riverside-pine-chalet"
        assert mock_storage.get_object_json.called

    asyncio.run(run())

