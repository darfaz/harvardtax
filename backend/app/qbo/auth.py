import secrets
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import httpx
from app.config import settings

router = APIRouter(prefix="/auth/qbo", tags=["QBO Auth"])

QBO_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QBO_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QBO_REVOKE_URL = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"

_oauth_states: dict[str, dict] = {}


@router.get("/connect")
async def connect(entity_id: str):
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {"entity_id": entity_id}
    params = {
        "client_id": settings.qbo_client_id,
        "redirect_uri": settings.qbo_redirect_uri,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "state": state,
    }
    return RedirectResponse(f"{QBO_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def callback(code: str, state: str, realmId: str):
    if state not in _oauth_states:
        raise HTTPException(400, "Invalid state")
    entity_id = _oauth_states.pop(state)["entity_id"]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            QBO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.qbo_redirect_uri,
            },
            auth=(settings.qbo_client_id, settings.qbo_client_secret),
        )
    if response.status_code != 200:
        raise HTTPException(400, f"Token exchange failed: {response.text}")
    tokens = response.json()
    # TODO: Store in Supabase (requires db module)
    return RedirectResponse(f"{settings.frontend_url}/entities/{entity_id}?qbo=connected")


@router.post("/disconnect/{entity_id}")
async def disconnect(entity_id: str):
    # TODO: Implement with Supabase
    return {"status": "disconnected"}
