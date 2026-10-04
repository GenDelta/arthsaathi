import pytest
from httpx import AsyncClient
from app.repositories.consent import ConsentRepository
from app.core.consent import CURRENT_NOTICE_VERSION, PURPOSE_STATEMENT_PROCESSING

@pytest.mark.asyncio
async def test_consent_grant_and_withdraw(async_client: AsyncClient):
    from app.core.security import create_access_token
    token = create_access_token("user_123", "USER", None)
    token_headers = {"Authorization": f"Bearer {token}"}
    # 1. Initially no consent
    res = await async_client.get("/api/consent/status", headers=token_headers)
    assert res.status_code == 200
    assert len(res.json()["consents"]) == 0

    # 2. Grant consent
    res = await async_client.post("/api/consent/grant", json={"purposes": [PURPOSE_STATEMENT_PROCESSING]}, headers=token_headers)
    assert res.status_code == 200

    res = await async_client.get("/api/consent/status", headers=token_headers)
    assert res.status_code == 200
    consents = res.json()["consents"]
    assert len(consents) == 1
    assert consents[0]["purpose"] == PURPOSE_STATEMENT_PROCESSING
    assert consents[0]["granted"] is True

    # 3. Withdraw consent
    res = await async_client.post("/api/consent/withdraw", json={"purpose": PURPOSE_STATEMENT_PROCESSING}, headers=token_headers)
    assert res.status_code == 200

    res = await async_client.get("/api/consent/status", headers=token_headers)
    assert res.status_code == 200
    consents = res.json()["consents"]
    assert len(consents) == 1
    assert consents[0]["granted"] is False

@pytest.mark.asyncio
async def test_erase_data(async_client: AsyncClient):
    from app.core.security import create_access_token
    token = create_access_token("user_123", "USER", None)
    token_headers = {"Authorization": f"Bearer {token}"}
    res = await async_client.delete("/api/consent/erase", headers=token_headers)
    assert res.status_code == 200
    erased = res.json()["erased_tables"]
    assert "transactions" in erased
    assert "account_bindings" in erased
