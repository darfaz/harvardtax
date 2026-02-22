import os
import tempfile
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.db import supabase
from app.qbo.client import QBOClient
from app.mapping.engine import map_accounts_to_1065, calculate_1065_totals
from app.allocation.k1_allocator import allocate_pro_rata
from app.pdf.generator import generate_1065, generate_k1

router = APIRouter(prefix="/api/tax-returns", tags=["Tax Returns"])


@router.post("/{entity_id}/generate")
async def generate_tax_return(entity_id: str, tax_year: int):
    entity = supabase.table("entities").select("*").eq("id", entity_id).single().execute()
    if not entity.data:
        raise HTTPException(404, "Entity not found")

    qbo_conn = supabase.table("qbo_connections").select("*").eq("entity_id", entity_id).single().execute()
    if not qbo_conn.data:
        raise HTTPException(400, "No QBO connection. Connect QuickBooks first.")

    partners = supabase.table("partners").select("*").eq("entity_id", entity_id).execute()
    if not partners.data:
        raise HTTPException(400, "No partners configured. Upload operating agreement first.")

    client = QBOClient(qbo_conn.data["access_token"], qbo_conn.data["realm_id"])

    start_date = f"{tax_year}-01-01"
    end_date = f"{tax_year}-12-31"

    accounts = await client.get_chart_of_accounts()
    pnl = await client.get_profit_and_loss(start_date, end_date)
    balance_sheet = await client.get_balance_sheet(end_date)
    trial_balance = await client.get_trial_balance(start_date, end_date)

    mapping_result = map_accounts_to_1065(accounts)
    totals = calculate_1065_totals(mapping_result)

    tax_return = supabase.table("tax_returns").upsert({
        "entity_id": entity_id,
        "tax_year": tax_year,
        "status": "draft",
        "qbo_data": {
            "accounts": accounts,
            "pnl": pnl,
            "balance_sheet": balance_sheet,
        },
        "mapped_data": mapping_result.to_dict(),
    }).execute()

    schedule_k_totals = {
        "K-1": totals.get("22", 0),
        "K-5": totals.get("K-5", 0),
        "K-6a": totals.get("K-6a", 0),
        "K-13a": totals.get("K-13a", 0),
        "K-18a": totals.get("K-18a", 0),
    }

    allocations = allocate_pro_rata(schedule_k_totals, partners.data)

    output_dir = tempfile.mkdtemp()

    f1065_path = os.path.join(output_dir, f"1065_{tax_year}.pdf")
    generate_1065(entity.data, totals, f1065_path)

    k1_paths = []
    for alloc in allocations:
        partner = next(p for p in partners.data if p["id"] == alloc["partner_id"])
        k1_path = os.path.join(output_dir, f"K1_{partner['name']}_{tax_year}.pdf")
        generate_k1(entity.data, partner, alloc["allocations"], k1_path)
        k1_paths.append(k1_path)

        supabase.table("k1s").insert({
            "tax_return_id": tax_return.data[0]["id"],
            "partner_id": alloc["partner_id"],
            "allocations": alloc["allocations"],
            "generated_pdf_url": k1_path,
        }).execute()

    return {
        "status": "generated",
        "tax_year": tax_year,
        "form_1065": f1065_path,
        "k1_count": len(k1_paths),
        "unmapped_accounts": mapping_result.unmapped,
        "message": f"Generated 1065 + {len(k1_paths)} K-1s. Review unmapped accounts if any.",
    }


@router.get("/{entity_id}/{tax_year}/mapping")
async def get_mapping_review(entity_id: str, tax_year: int):
    tax_return = supabase.table("tax_returns").select("*").eq("entity_id", entity_id).eq("tax_year", tax_year).single().execute()
    if not tax_return.data:
        raise HTTPException(404, "No tax return found. Generate first.")
    return {
        "mapped_data": tax_return.data["mapped_data"],
        "unmapped_accounts": tax_return.data["mapped_data"].get("unmapped_accounts", []),
    }


@router.post("/{entity_id}/{tax_year}/override")
async def save_overrides(entity_id: str, tax_year: int, overrides: dict[str, str]):
    supabase.table("tax_returns").update({
        "mapping_overrides": overrides,
    }).eq("entity_id", entity_id).eq("tax_year", tax_year).execute()
    return {"status": "overrides_saved", "message": "Re-generate to apply overrides."}
