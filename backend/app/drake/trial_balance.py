"""
Drake Trial Balance Import Generator for 1065 Partnership Returns.

Generates Excel files matching Drake's Trial Balance Import template format.
The template structure (reverse-engineered from Drake's practice worksheets):

Layout: Two-panel spreadsheet
  LEFT SIDE (cols B-E): Balance Sheet
    - Current Assets (Cash, AR, Allowance, Inventory, Other)
    - Long-Term Assets (Depreciable, Accum Depr, Land, Investments, Other)
    - Current Liabilities (AP, Notes Payable)
    - Long-Term Liabilities (Mortgages, Other LT)
    - Partners' Equity (Capital, Current Year Income, Expenses)
  
  RIGHT SIDE (cols H-J): Income Statement
    - Revenue (Net Sales / Rental Income)
    - COGS (if applicable)
    - Expenses (itemized)
    - Other Income / Other Expenses (Separately stated K items)

Drake Import Mapping: Each row maps to a Drake screen/line automatically.
The template uses account titles that Drake recognizes and routes to the
correct 1065 form lines.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import datetime


@dataclass
class BalanceSheetEntry:
    """A single line on the balance sheet side."""
    account_title: str
    debit: float = 0.0
    credit: float = 0.0


@dataclass
class IncomeStatementEntry:
    """A single line on the income statement side."""
    account_title: str
    amount: float = 0.0


@dataclass
class PartnerInfo:
    """Partner/investor information for K-1 generation."""
    id: str
    name: str
    tin: str = ""  # SSN or EIN
    address: str = ""
    ownership_pct: float = 0.0
    capital_beginning: float = 0.0
    capital_contributions: float = 0.0
    capital_withdrawals: float = 0.0
    capital_ending: float = 0.0
    profit_pct: float = 0.0
    loss_pct: float = 0.0


@dataclass
class InvestmentFundData:
    """
    Data model for an investment fund / SPV series.
    Designed for the Garage Syndicate use case:
    - Master series LLC with sub-series
    - Each series is a separate partnership for tax purposes
    - Investors contribute capital, fund invests in startups
    - Exit events generate income + distributions
    """
    # Entity info
    entity_name: str = ""
    ein: str = ""
    tax_year: int = 2025
    date_formed: str = ""
    entity_type: str = "partnership"  # LLC taxed as partnership
    state: str = "DE"  # Delaware
    
    # Balance sheet - Assets
    cash: float = 0.0
    accounts_receivable: float = 0.0
    other_current_assets: float = 0.0
    investments_at_cost: float = 0.0  # underlying securities/SAFE/equity
    investments_fmv: float = 0.0  # fair market value (for reporting)
    other_assets: float = 0.0
    
    # Balance sheet - Liabilities
    accounts_payable: float = 0.0
    notes_payable: float = 0.0
    other_liabilities: float = 0.0
    
    # Income
    investment_income: float = 0.0  # dividends, interest
    capital_gains_short: float = 0.0
    capital_gains_long: float = 0.0
    other_income: float = 0.0
    
    # Distributions received from underlying
    distributions_received: float = 0.0
    
    # Expenses
    management_fees: float = 0.0
    legal_fees: float = 0.0
    accounting_fees: float = 0.0
    admin_fees: float = 0.0  # platform fees (Carta, etc.)
    other_expenses: float = 0.0
    
    # Exit event details
    exit_proceeds_cash: float = 0.0
    exit_proceeds_stock: float = 0.0  # FMV of stock received
    exit_cost_basis: float = 0.0  # original investment cost
    
    # Partners
    partners: list = field(default_factory=list)  # list of PartnerInfo
    
    # Distributions to partners
    distributions_to_partners: float = 0.0


# ─── Drake Account Title Mappings ─────────────────────────────────
# These titles must match what Drake expects for automatic line mapping.
# Based on reverse-engineering the practice worksheet templates.

DRAKE_1065_BALANCE_SHEET = {
    # Current Assets
    "cash": "Cash",
    "accounts_receivable": "Accounts receivable",
    "allowance_bad_debts": "Allowance for bad debts",
    "inventory": "Ending inventory",
    "other_current_assets": "Other current assets",
    # Long-Term Assets
    "investments": "Other investments",
    "other_assets": "Other assets",
    # Current Liabilities
    "accounts_payable": "Accounts payable",
    "notes_payable": "Notes payable",
    # Long-Term Liabilities
    "other_lt_liabilities": "Other long-term liabilities",
    # Partners' Equity
    "partners_capital": "Partners' capital",
    "current_year_income": "Current year income",
    "expenses": "Expenses",
}

DRAKE_1065_INCOME_CATEGORIES = {
    # These map to specific Drake 1065 screens/lines
    "net_sales": "Net Sales",
    "cogs": "COGS",
    "capital_gain_loss": "Net gain (loss) under Sec 1231",
    "other_income": "Other income (loss)",
    # Deductions
    "management_fees": "Management fees",
    "legal_fees": "Legal and professional services",
    "accounting_fees": "Accounting",
    "admin_fees": "Other deductions",
    "other_expenses": "Other deductions",
    # Separately stated items (K-1 items)
    "interest_income": "Interest income",
    "dividend_income": "Dividend income",
    "st_capital_gain": "Net short-term capital gain (loss)",
    "lt_capital_gain": "Net long-term capital gain (loss)",
    "charitable": "Charitable contributions",
    "sec_199a": "Section 199A",
}


def build_trial_balance(fund: InvestmentFundData) -> dict:
    """
    Build a Drake-compatible trial balance from fund data.
    
    Returns a dict with:
      - balance_sheet: list of BalanceSheetEntry
      - income_statement: list of IncomeStatementEntry
      - totals: summary numbers
      - partner_allocations: per-partner K-1 data
    """
    bs_entries = []
    is_entries = []
    
    # ─── Balance Sheet ─────────────────────────────────────
    # Assets (debits)
    if fund.cash:
        bs_entries.append(BalanceSheetEntry("Cash", debit=fund.cash))
    if fund.accounts_receivable:
        bs_entries.append(BalanceSheetEntry("Accounts receivable", debit=fund.accounts_receivable))
    if fund.other_current_assets:
        bs_entries.append(BalanceSheetEntry("Other current assets", debit=fund.other_current_assets))
    
    # Investments — the key asset for a fund
    total_investments = fund.investments_at_cost
    if fund.exit_proceeds_stock:
        # Stock received in exit sits as an investment asset
        total_investments += fund.exit_proceeds_stock
    if total_investments:
        bs_entries.append(BalanceSheetEntry("Other investments", debit=total_investments))
    
    if fund.other_assets:
        bs_entries.append(BalanceSheetEntry("Other assets", debit=fund.other_assets))
    
    # Liabilities (credits)
    if fund.accounts_payable:
        bs_entries.append(BalanceSheetEntry("Accounts payable", credit=fund.accounts_payable))
    if fund.notes_payable:
        bs_entries.append(BalanceSheetEntry("Notes payable", credit=fund.notes_payable))
    if fund.other_liabilities:
        bs_entries.append(BalanceSheetEntry("Other long-term liabilities", credit=fund.other_liabilities))
    
    # ─── Income Statement ──────────────────────────────────
    
    # Capital gains from exit events
    net_gain = (fund.exit_proceeds_cash + fund.exit_proceeds_stock) - fund.exit_cost_basis
    if net_gain != 0:
        # Determine short vs long-term based on holding period
        # For now, assume long-term (most VC exits are >1yr)
        if fund.capital_gains_long:
            is_entries.append(IncomeStatementEntry(
                "Net long-term capital gain (loss)", fund.capital_gains_long
            ))
        elif net_gain:
            is_entries.append(IncomeStatementEntry(
                "Net long-term capital gain (loss)", net_gain
            ))
    
    if fund.capital_gains_short:
        is_entries.append(IncomeStatementEntry(
            "Net short-term capital gain (loss)", fund.capital_gains_short
        ))
    
    # Investment income
    if fund.investment_income:
        is_entries.append(IncomeStatementEntry("Interest income", fund.investment_income))
    
    if fund.other_income:
        is_entries.append(IncomeStatementEntry("Other income (loss)", fund.other_income))
    
    # Expenses
    if fund.management_fees:
        is_entries.append(IncomeStatementEntry("Management fees", fund.management_fees))
    if fund.legal_fees:
        is_entries.append(IncomeStatementEntry("Legal and professional services", fund.legal_fees))
    if fund.accounting_fees:
        is_entries.append(IncomeStatementEntry("Accounting", fund.accounting_fees))
    if fund.admin_fees:
        is_entries.append(IncomeStatementEntry("Other deductions", fund.admin_fees))
    if fund.other_expenses:
        is_entries.append(IncomeStatementEntry("Other expenses", fund.other_expenses))
    
    # ─── Calculate Totals ──────────────────────────────────
    total_assets = sum(e.debit for e in bs_entries) - sum(
        e.credit for e in bs_entries if e.account_title not in [
            "Accounts payable", "Notes payable", "Other long-term liabilities"
        ]
    )
    total_liabilities = sum(
        e.credit for e in bs_entries if e.account_title in [
            "Accounts payable", "Notes payable", "Other long-term liabilities"
        ]
    )
    
    total_income = sum(
        e.amount for e in is_entries
        if not any(kw in e.account_title.lower() for kw in [
            "fees", "deduction", "expense", "accounting", "legal"
        ])
    )
    total_expenses = sum(
        e.amount for e in is_entries
        if any(kw in e.account_title.lower() for kw in [
            "fees", "deduction", "expense", "accounting", "legal"
        ])
    )
    net_income = total_income - total_expenses
    
    # ─── Partner Allocations ───────────────────────────────
    partner_allocations = _allocate_to_partners(fund, net_income, total_income, total_expenses)
    
    # Partners' Equity for balance sheet
    total_partner_capital = sum(p.capital_ending for p in fund.partners) if fund.partners else 0
    if not total_partner_capital:
        # Calculate from beginning + income - distributions
        total_partner_capital = sum(
            p.capital_beginning + p.capital_contributions - p.capital_withdrawals
            for p in fund.partners
        ) if fund.partners else 0
        total_partner_capital += net_income - fund.distributions_to_partners
    
    return {
        "entity_name": fund.entity_name,
        "ein": fund.ein,
        "tax_year": fund.tax_year,
        "balance_sheet": bs_entries,
        "income_statement": is_entries,
        "total_assets": sum(e.debit for e in bs_entries),
        "total_liabilities": total_liabilities,
        "total_equity": total_partner_capital,
        "net_income": net_income,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "partner_allocations": partner_allocations,
        "distributions_to_partners": fund.distributions_to_partners,
    }


def _allocate_to_partners(
    fund: InvestmentFundData,
    net_income: float,
    total_income: float, 
    total_expenses: float,
) -> list[dict]:
    """Pro-rata allocation of income/loss to each partner."""
    if not fund.partners:
        return []
    
    allocations = []
    for partner in fund.partners:
        pct = Decimal(str(partner.ownership_pct)) / Decimal("100")
        
        alloc = {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "tin": partner.tin,
            "address": partner.address,
            "ownership_pct": partner.ownership_pct,
            "profit_loss_pct": partner.profit_pct or partner.ownership_pct,
            # Capital account (K-1 Part II, Item L)
            "capital_beginning": partner.capital_beginning,
            "capital_contributions": partner.capital_contributions,
            "capital_share_of_income": float(
                (Decimal(str(net_income)) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ),
            "capital_withdrawals": partner.capital_withdrawals,
            "capital_ending": partner.capital_ending,
            # K-1 income items
            "ordinary_income": float(
                (Decimal(str(fund.other_income or 0)) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ),
            "net_st_capital_gain": float(
                (Decimal(str(fund.capital_gains_short or 0)) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ),
            "net_lt_capital_gain": float(
                (Decimal(str(fund.capital_gains_long or net_income)) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ),
            "distributions": float(
                (Decimal(str(fund.distributions_to_partners)) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            ),
        }
        
        # Calculate ending capital if not provided
        if not alloc["capital_ending"]:
            alloc["capital_ending"] = (
                alloc["capital_beginning"]
                + alloc["capital_contributions"]
                + alloc["capital_share_of_income"]
                - alloc["capital_withdrawals"]
                - alloc["distributions"]
            )
        
        allocations.append(alloc)
    
    return allocations
