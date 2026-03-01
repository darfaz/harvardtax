"""
Drake Integration API endpoints.
Generates Drake-compatible trial balance import files for 1065 returns.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os

from app.drake.trial_balance import InvestmentFundData, PartnerInfo
from app.drake.excel_generator import generate_full_package


router = APIRouter(prefix="/api/drake", tags=["drake"])


class PartnerInput(BaseModel):
    id: str
    name: str
    tin: str = ""
    address: str = ""
    ownership_pct: float
    capital_beginning: float = 0.0
    capital_contributions: float = 0.0
    capital_withdrawals: float = 0.0
    capital_ending: float = 0.0
    profit_pct: float = 0.0
    loss_pct: float = 0.0


class FundInput(BaseModel):
    entity_name: str
    ein: str = ""
    tax_year: int = 2025
    date_formed: str = ""
    state: str = "DE"
    # Assets
    cash: float = 0.0
    accounts_receivable: float = 0.0
    other_current_assets: float = 0.0
    investments_at_cost: float = 0.0
    investments_fmv: float = 0.0
    other_assets: float = 0.0
    # Liabilities
    accounts_payable: float = 0.0
    notes_payable: float = 0.0
    other_liabilities: float = 0.0
    # Income
    investment_income: float = 0.0
    capital_gains_short: float = 0.0
    capital_gains_long: float = 0.0
    other_income: float = 0.0
    # Exit
    exit_proceeds_cash: float = 0.0
    exit_proceeds_stock: float = 0.0
    exit_cost_basis: float = 0.0
    # Expenses
    management_fees: float = 0.0
    legal_fees: float = 0.0
    accounting_fees: float = 0.0
    admin_fees: float = 0.0
    other_expenses: float = 0.0
    # Distributions
    distributions_to_partners: float = 0.0
    # Partners
    partners: list[PartnerInput] = []


@router.post("/generate")
async def generate_drake_package(fund_input: FundInput):
    """
    Generate Drake Trial Balance Import package.
    Returns paths to generated files and summary data.
    """
    partners = [
        PartnerInfo(
            id=p.id, name=p.name, tin=p.tin, address=p.address,
            ownership_pct=p.ownership_pct, capital_beginning=p.capital_beginning,
            capital_contributions=p.capital_contributions,
            capital_withdrawals=p.capital_withdrawals,
            capital_ending=p.capital_ending,
            profit_pct=p.profit_pct or p.ownership_pct,
            loss_pct=p.loss_pct or p.ownership_pct,
        )
        for p in fund_input.partners
    ]
    
    fund = InvestmentFundData(
        entity_name=fund_input.entity_name,
        ein=fund_input.ein,
        tax_year=fund_input.tax_year,
        date_formed=fund_input.date_formed,
        state=fund_input.state,
        cash=fund_input.cash,
        accounts_receivable=fund_input.accounts_receivable,
        other_current_assets=fund_input.other_current_assets,
        investments_at_cost=fund_input.investments_at_cost,
        investments_fmv=fund_input.investments_fmv,
        other_assets=fund_input.other_assets,
        accounts_payable=fund_input.accounts_payable,
        notes_payable=fund_input.notes_payable,
        other_liabilities=fund_input.other_liabilities,
        investment_income=fund_input.investment_income,
        capital_gains_short=fund_input.capital_gains_short,
        capital_gains_long=fund_input.capital_gains_long,
        other_income=fund_input.other_income,
        exit_proceeds_cash=fund_input.exit_proceeds_cash,
        exit_proceeds_stock=fund_input.exit_proceeds_stock,
        exit_cost_basis=fund_input.exit_cost_basis,
        management_fees=fund_input.management_fees,
        legal_fees=fund_input.legal_fees,
        accounting_fees=fund_input.accounting_fees,
        admin_fees=fund_input.admin_fees,
        other_expenses=fund_input.other_expenses,
        distributions_to_partners=fund_input.distributions_to_partners,
        partners=partners,
    )
    
    result = generate_full_package(fund, "output")
    return result


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated Excel file."""
    filepath = f"output/{filename}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="application/vnd.ms-excel", filename=filename)
