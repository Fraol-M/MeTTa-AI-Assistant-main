"""
Integration tests for chunk endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from qdrant_client.models import ScoredPoint
from app.main import app


@pytest.mark.integration
class TestChunkEndpoints:
    """Test chunk API endpoints."""

    @pytest.mark.asyncio
    async def test_ingest_repository(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token
    ):
        """Test repository ingestion endpoint."""
        mock_mongo_collection.insert_many = AsyncMock()
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        with patch('app.routers.chunks.ingest_pipeline') as mock_ingest:
            mock_ingest.return_value = None
            
            response = await async_client.post(
                "/api/chunks/ingest?repo_url=https://github.com/test/repo&chunk_size=1000",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "message" in data

    @pytest.mark.asyncio
    async def test_ingest_repository_unauthorized(self, async_client: AsyncClient):
        """Test ingestion without authentication."""
        response = await async_client.post(
            "/api/chunks/ingest?repo_url=https://github.com/test/repo"
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_chunks(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token, sample_chunk_data
    ):
        """Test listing chunks."""
        mock_cursor = AsyncMock()
        chunks_list = [sample_chunk_data]
        mock_cursor.__aiter__ = MagicMock(return_value=iter(chunks_list))
        mock_mongo_collection.find = MagicMock(return_value=mock_cursor)
        
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.get(
            "/api/chunks/?project=test_project",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_chunk_by_id(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token, sample_chunk_data
    ):
        """Test getting a specific chunk (used in update flow)."""
        mock_mongo_collection.find_one = AsyncMock(return_value=sample_chunk_data)
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.get(
            "/api/chunks/",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_chunk(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token, sample_chunk_data
    ):
        """Test updating a chunk."""
        mock_mongo_collection.find_one = AsyncMock(return_value=sample_chunk_data)
        
        update_result = MagicMock()
        update_result.modified_count = 1
        mock_mongo_collection.update_one = AsyncMock(return_value=update_result)
        
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.patch(
            "/api/chunks/test_chunk_123",
            json={"source": "documentation"},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "chunk" in data

    @pytest.mark.asyncio
    async def test_update_chunk_not_found(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token
    ):
        """Test updating a non-existent chunk."""
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.patch(
            "/api/chunks/nonexistent",
            json={"source": "documentation"},
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_chunk(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token, sample_chunk_data
    ):
        """Test deleting a chunk."""
        mock_mongo_collection.find_one = AsyncMock(return_value=sample_chunk_data)
        
        delete_result = MagicMock()
        delete_result.deleted_count = 1
        mock_mongo_collection.delete_one = AsyncMock(return_value=delete_result)
        
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.delete(
            "/api/chunks/test_chunk_123",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_embed_pipeline(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, mock_qdrant_client,
        mock_embedding_model, test_token
    ):
        """Test embedding pipeline endpoint."""
        sample_chunks = [
            {
                "chunkId": "chunk_1",
                "chunk": "Test chunk 1",
                "isEmbedded": False
            }
        ]
        
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = MagicMock(return_value=iter(sample_chunks))
        mock_mongo_collection.find = MagicMock(return_value=mock_cursor)
        
        update_result = MagicMock()
        update_result.modified_count = 1
        mock_mongo_collection.update_many = AsyncMock(return_value=update_result)
        
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        app.state.qdrant_client = mock_qdrant_client
        app.state.embedding_model = mock_embedding_model
        
        with patch('app.routers.chunks.embedding_pipeline') as mock_pipeline:
            mock_pipeline.return_value = 1
            
            response = await async_client.post(
                "/api/chunks/embed",
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    @pytest.mark.asyncio
    async def test_semantic_search(
        self, async_client: AsyncClient, mock_qdrant_client, mock_embedding_model, test_token
    ):
        """Test semantic search endpoint."""
        # Mock Qdrant search results
        mock_point = MagicMock()
        mock_point.payload = {
            "chunk": "Test chunk content",
            "source": "code",
            "project": "test_project"
        }
        mock_point.score = 0.9
        mock_point.id = "test_id"
        
        mock_qdrant_client.search = AsyncMock(return_value=[mock_point])
        app.state.qdrant_client = mock_qdrant_client
        app.state.embedding_model = mock_embedding_model
        
        response = await async_client.get(
            "/api/chunks/search?q=test query&top_k=5",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data

    @pytest.mark.asyncio
    async def test_semantic_search_invalid_query(self, async_client: AsyncClient, test_token):
        """Test semantic search with invalid query."""
        response = await async_client.get(
            "/api/chunks/search?q=&top_k=5",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 422  # Validation error

