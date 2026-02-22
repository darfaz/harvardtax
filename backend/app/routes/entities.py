from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.db import supabase
from app.extraction.agreement_parser import parse_operating_agreement

router = APIRouter(prefix="/api/entities", tags=["Entities"])


class EntityCreate(BaseModel):
    name: str
    ein: str | None = None
    entity_type: str = "LLC"


@router.post("/")
async def create_entity(entity: EntityCreate, tenant_id: str):
    result = supabase.table("entities").insert({
        "tenant_id": tenant_id,
        "name": entity.name,
        "ein": entity.ein,
        "entity_type": entity.entity_type,
    }).execute()
    return result.data[0]


@router.get("/{entity_id}")
async def get_entity(entity_id: str):
    result = supabase.table("entities").select("*, partners(*), qbo_connections(*)").eq("id", entity_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Entity not found")
    return result.data


@router.post("/{entity_id}/upload-agreement")
async def upload_agreement(entity_id: str, file: UploadFile = File(...)):
    content = await file.read()
    extracted = await parse_operating_agreement(content, file.filename)
    supabase.table("operating_agreements").insert({
        "entity_id": entity_id,
        "extracted_data": extracted,
    }).execute()
    return {
        "status": "extracted",
        "data": extracted,
        "message": "Please review and confirm the extracted data.",
    }


@router.post("/{entity_id}/confirm-partners")
async def confirm_partners(entity_id: str, partners: list[dict]):
    for p in partners:
        supabase.table("partners").insert({
            "entity_id": entity_id,
            **p,
        }).execute()
    supabase.table("operating_agreements").update({
        "confirmed_at": "now()",
    }).eq("entity_id", entity_id).is_("confirmed_at", "null").execute()
    return {"status": "confirmed", "partner_count": len(partners)}
