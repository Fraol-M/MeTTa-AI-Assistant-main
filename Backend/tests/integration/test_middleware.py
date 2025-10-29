"""
Integration tests for middleware.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app


@pytest.mark.integration
class TestAuthMiddleware:
    """Test authentication middleware."""

    @pytest.mark.asyncio
    async def test_protected_route_without_token(self, async_client: AsyncClient):
        """Test that protected routes require authentication."""
        response = await async_client.get("/api/chunks/")
        
        assert response.status_code == 401
        assert "No token provided" in response.json()["detail"] or "token" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_protected_route_with_invalid_token(self, async_client: AsyncClient):
        """Test protected route with invalid token."""
        response = await async_client.get(
            "/api/chunks/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_route_with_expired_token(
        self, async_client: AsyncClient, expired_token
    ):
        """Test protected route with expired token."""
        response = await async_client.get(
            "/api/chunks/",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_route_without_token(self, async_client: AsyncClient):
        """Test that auth routes don't require token."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        
        # Auth endpoints should be accessible
        response = await async_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "test"}
        )
        # This should fail due to invalid credentials, not missing token
        assert response.status_code in [401, 422]

    @pytest.mark.asyncio
    async def test_protected_route_with_valid_token(
        self, async_client: AsyncClient, test_token, mock_mongo_collection, mock_mongo_db
    ):
        """Test that protected routes work with valid token."""
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = MagicMock(return_value=iter([]))
        mock_mongo_collection.find = MagicMock(return_value=mock_cursor)
        mock_mongo_db.get_collection = lambda name: mock_mongo_collection
        app.state.mongo_db = mock_mongo_db
        
        response = await async_client.get(
            "/api/chunks/",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        # Should not be 401 (unauthorized)
        assert response.status_code != 401

