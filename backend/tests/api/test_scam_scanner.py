import asyncio

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.repositories.user import UserRepository


# Mock the OCR function

@pytest.fixture(autouse=True)
def mock_ocr(monkeypatch):
    from app.api import scam_scanner
    async def async_mock(x): return "MOCK_OCR_TEXT"
    monkeypatch.setattr(scam_scanner, "extract_text", async_mock)



# Mock the scam_graph graph
@pytest.fixture(autouse=True)
def mock_scam_graph(monkeypatch):
    import app.agents.scam.graph
    
    class DummyGraph:
        async def ainvoke(self, state):
            # Return dummy state for successful analysis
            return {
                **state,
                "risk_score": 0.8,
                "risk_summary": "High risk detected",
                "matched_clauses": [{"id": "test-clause-1"}]
            }
    
    monkeypatch.setattr(app.agents.scam.graph, "scam_graph", DummyGraph())


@pytest.mark.asyncio
async def test_scam_scanner_flow(async_client: AsyncClient):
    """Test the full Scam Scanner API flow."""
    # Create user
    user_repo = UserRepository()
    user = await user_repo.create_user(
        name="Test User",
        phone_number="+910000000001",
        password_hash="dummy_hash",
        language_pref="en",
    )
    
    # Generate token
    token = create_access_token(user.id, user.role, user.organization_id)

    # Grant consent
    await async_client.post("/api/consent/grant", json={"purposes": ["STATEMENT_PROCESSING"]}, headers={"Authorization": f"Bearer {token}"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Init scan
    file_content = b"fake image bytes"
    files = {"file": ("test.png", file_content, "image/png")}
    response = await async_client.post("/api/scan-document", files=files, headers=headers)
    assert response.status_code == 202
    
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "PENDING_VERIFICATION"
    assert data["extracted_text"] == "MOCK_OCR_TEXT"
    
    doc_id = data["document_id"]
    
    # 2. Verify scan
    verify_payload = {"verified_text": "User manually corrected text"}
    response = await async_client.post(f"/api/scan-document/{doc_id}/verify", json=verify_payload, headers=headers)
    assert response.status_code == 202
    
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "ANALYZING"
    
    # Give the background task a moment to finish
    await asyncio.sleep(0.5)
    
    # 3. Poll for status
    response = await async_client.get(f"/api/scan-document/{doc_id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["document_id"] == doc_id
    assert data["status"] == "ANALYZED"
    assert data["risk_level"] == "HIGH"
    assert data["risk_summary"] == "High risk detected"

@pytest.mark.asyncio
async def test_scam_scanner_tenant_isolation(async_client: AsyncClient):
    """Test that a user cannot fetch another user's document (returns 404)."""
    user_repo = UserRepository()
    user1 = await user_repo.create_user(
        name="User One", phone_number="+910000000011", password_hash="hash", language_pref="en"
    )
    user2 = await user_repo.create_user(
        name="User Two", phone_number="+910000000022", password_hash="hash", language_pref="en"
    )
    
    token1 = create_access_token(user1.id, user1.role, user1.organization_id)
    await async_client.post("/api/consent/grant", json={"purposes": ["STATEMENT_PROCESSING"]}, headers={"Authorization": f"Bearer {token1}"})
    token2 = create_access_token(user2.id, user2.role, user2.organization_id)
    await async_client.post("/api/consent/grant", json={"purposes": ["STATEMENT_PROCESSING"]}, headers={"Authorization": f"Bearer {token2}"})
    
    # User 1 creates a document
    file_content = b"fake image bytes"
    files = {"file": ("test.png", file_content, "image/png")}
    response = await async_client.post("/api/scan-document", files=files, headers={"Authorization": f"Bearer {token1}"})
    doc_id = response.json()["document_id"]
    
    # User 2 attempts to fetch it
    response = await async_client.get(f"/api/scan-document/{doc_id}", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 404
