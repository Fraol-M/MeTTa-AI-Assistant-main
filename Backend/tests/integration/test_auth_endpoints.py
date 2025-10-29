"""
Integration tests for authentication endpoints.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from bson import ObjectId
from app.main import app
from app.db.users import UserRole


@pytest.mark.integration
class TestAuthEndpoints:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_signup_success(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_user_data
    ):
        """Test successful user signup."""
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        
        insert_result = MagicMock()
        insert_result.inserted_id = ObjectId()
        mock_mongo_collection.insert_one = AsyncMock(return_value=insert_result)
        
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.post(
            "/api/auth/signup",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
                "role": "user"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_signup_duplicate_email(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_user_data
    ):
        """Test signup with duplicate email."""
        mock_mongo_collection.find_one = AsyncMock(
            return_value={"email": test_user_data["email"]}
        )
        
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.post(
            "/api/auth/signup",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
                "role": "user"
            }
        )
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_success(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_user_data
    ):
        """Test successful login."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(test_user_data["password"])
        
        mock_user = {
            "_id": ObjectId(),
            "email": test_user_data["email"],
            "hashed_password": hashed,
            "role": "user"
        }
        
        mock_mongo_collection.find_one = AsyncMock(return_value=mock_user)
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_user_data
    ):
        """Test login with invalid credentials."""
        mock_mongo_collection.find_one = AsyncMock(return_value=None)
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self, async_client: AsyncClient, mock_mongo_collection, mock_mongo_db, test_token
    ):
        """Test successful token refresh."""
        from jose import jwt
        import os
        
        payload = jwt.decode(test_token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
        payload["type"] = "refresh"
        refresh_token = jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
        
        mock_user = {
            "_id": ObjectId(payload["sub"]),
            "email": "test@example.com",
            "role": "user"
        }
        
        mock_mongo_collection.find_one = AsyncMock(return_value=mock_user)
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_expired(self, async_client: AsyncClient, expired_token):
        """Test refresh with expired token."""
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired_token}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_invalid_format(self, async_client: AsyncClient):
        """Test login with invalid request format."""
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "test@example.com"}  # Missing password
        )
        
        assert response.status_code == 422  # Validation error

