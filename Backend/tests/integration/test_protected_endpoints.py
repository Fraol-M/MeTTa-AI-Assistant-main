"""
Integration tests for protected endpoints.
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.integration
class TestProtectedEndpoints:
    """Test protected API endpoints."""

    @pytest.mark.asyncio
    async def test_admin_only_with_admin_token(
        self, async_client: AsyncClient, admin_token
    ):
        """Test admin-only endpoint with admin token."""
        response = await async_client.get(
            "/api/protected/admin-only",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Admin only route" in data["message"]

    @pytest.mark.asyncio
    async def test_admin_only_with_user_token(
        self, async_client: AsyncClient, test_token
    ):
        """Test admin-only endpoint with regular user token (should fail)."""
        response = await async_client.get(
            "/api/protected/admin-only",
            headers={"Authorization": f"Bearer {test_token}"}
        )
        
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_only_without_token(self, async_client: AsyncClient):
        """Test admin-only endpoint without token."""
        response = await async_client.get("/api/protected/admin-only")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_only_with_expired_token(
        self, async_client: AsyncClient, expired_token
    ):
        """Test admin-only endpoint with expired token."""
        response = await async_client.get(
            "/api/protected/admin-only",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401

