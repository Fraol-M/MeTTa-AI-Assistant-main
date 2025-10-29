"""
Unit tests for database operations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from pymongo.errors import BulkWriteError
from bson import ObjectId
from app.db.db import (
    insert_chunk,
    insert_chunks,
    get_chunk_by_id,
    get_chunks,
    update_chunk,
    update_chunks,
    delete_chunk,
    update_embedding_status,
    ChunkSchema
)
from app.db.users import create_user, UserCreate, UserRole


@pytest.mark.unit
class TestDatabaseOperations:
    """Test database CRUD operations."""

    @pytest.mark.asyncio
    async def test_insert_chunk_success(self, mock_mongo_collection, sample_chunk_data):
        """Test successful chunk insertion."""
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        
        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId()
        mock_mongo_collection.insert_one = AsyncMock(return_value=insert_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await insert_chunk(sample_chunk_data, mock_db)
        
        assert result == sample_chunk_data["chunkId"]
        mock_mongo_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_insert_chunk_duplicate(self, mock_mongo_collection, sample_chunk_data):
        """Test that duplicate chunks are not inserted."""
        mock_mongo_collection.find_one = AsyncMock(
            return_value={"chunkId": sample_chunk_data["chunkId"]}
        )
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await insert_chunk(sample_chunk_data, mock_db)
        
        assert result is None
        mock_mongo_collection.insert_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_insert_chunk_validation_error(self, mock_mongo_collection):
        """Test that invalid chunk data is rejected."""
        invalid_data = {"chunkId": "test"}  # Missing required fields
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await insert_chunk(invalid_data, mock_db)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_insert_chunks_success(self, mock_mongo_collection):
        """Test bulk chunk insertion."""
        chunks = [
            {
                "chunkId": f"chunk_{i}",
                "source": "code",
                "chunk": f"Test chunk {i}",
                "isEmbedded": False
            }
            for i in range(3)
        ]
        
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        
        insert_result = MagicMock()
        insert_result.inserted_ids = [ObjectId() for _ in range(3)]
        mock_mongo_collection.insert_many = AsyncMock(return_value=insert_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await insert_chunks(chunks, mock_db)
        
        assert len(result) == 3
        mock_mongo_collection.insert_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_chunk_by_id(self, mock_mongo_collection, sample_chunk_data):
        """Test retrieving a chunk by ID."""
        mock_mongo_collection.find_one = AsyncMock(return_value=sample_chunk_data)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await get_chunk_by_id("test_chunk_123", mock_db)
        
        assert result == sample_chunk_data
        mock_mongo_collection.find_one.assert_called_once_with(
            {"chunkId": "test_chunk_123"},
            {"_id": 0}
        )

    @pytest.mark.asyncio
    async def test_get_chunks(self, mock_mongo_collection, sample_chunk_data):
        """Test retrieving multiple chunks."""
        mock_cursor = AsyncMock()
        chunks_list = [sample_chunk_data, {**sample_chunk_data, "chunkId": "chunk_2"}]
        mock_cursor.__aiter__ = MagicMock(return_value=iter(chunks_list))
        
        mock_mongo_collection.find = MagicMock(return_value=mock_cursor)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await get_chunks({"project": "test_project"}, limit=10, mongo_db=mock_db)
        
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_update_chunk(self, mock_mongo_collection):
        """Test updating a chunk."""
        update_result = MagicMock()
        update_result.modified_count = 1
        mock_mongo_collection.update_one = AsyncMock(return_value=update_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await update_chunk("test_chunk_123", {"source": "documentation"}, mock_db)
        
        assert result == 1
        mock_mongo_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_chunks(self, mock_mongo_collection):
        """Test updating multiple chunks."""
        update_result = MagicMock()
        update_result.modified_count = 3
        mock_mongo_collection.update_many = AsyncMock(return_value=update_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await update_chunks(
            {"project": "test_project"},
            {"isEmbedded": True},
            mock_db
        )
        
        assert result == 3

    @pytest.mark.asyncio
    async def test_delete_chunk(self, mock_mongo_collection):
        """Test deleting a chunk."""
        delete_result = MagicMock()
        delete_result.deleted_count = 1
        mock_mongo_collection.delete_one = AsyncMock(return_value=delete_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await delete_chunk("test_chunk_123", mock_db)
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_update_embedding_status_single(self, mock_mongo_collection):
        """Test updating embedding status for a single chunk."""
        update_result = MagicMock()
        update_result.modified_count = 1
        mock_mongo_collection.update_one = AsyncMock(return_value=update_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await update_embedding_status("chunk_123", True, mock_db)
        
        assert result == 1

    @pytest.mark.asyncio
    async def test_update_embedding_status_multiple(self, mock_mongo_collection):
        """Test updating embedding status for multiple chunks."""
        update_result = MagicMock()
        update_result.modified_count = 3
        mock_mongo_collection.update_many = AsyncMock(return_value=update_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        result = await update_embedding_status(["chunk_1", "chunk_2", "chunk_3"], True, mock_db)
        
        assert result == 3


@pytest.mark.unit
class TestUserOperations:
    """Test user database operations."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_mongo_collection, test_user_data):
        """Test successful user creation."""
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        
        insert_result = MagicMock()
        new_id = ObjectId()
        insert_result.inserted_id = new_id
        mock_mongo_collection.insert_one = AsyncMock(return_value=insert_result)
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        user_create = UserCreate(**test_user_data)
        result = await create_user(user_create, mock_db)
        
        assert result == new_id
        mock_mongo_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, mock_mongo_collection, test_user_data):
        """Test that duplicate emails are rejected."""
        mock_mongo_collection.find_one = AsyncMock(
            return_value={"email": test_user_data["email"]}
        )
        
        mock_db = AsyncMock()
        mock_db.get_collection = lambda name: mock_mongo_collection
        
        user_create = UserCreate(**test_user_data)
        
        with pytest.raises(ValueError, match="already registered"):
            await create_user(user_create, mock_db)

