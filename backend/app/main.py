from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(title="HarvardTax API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.qbo.auth import router as qbo_auth_router
from app.routes.entities import router as entities_router
from app.routes.tax_returns import router as tax_returns_router

app.include_router(qbo_auth_router)
app.include_router(entities_router)
app.include_router(tax_returns_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
