"""
Generates Drake-compatible Trial Balance Import Excel files for 1065 returns.

Output format matches Drake's template structure exactly:
- .xls format (Excel 97-2003) — required by Drake's macro-enabled import
- Two-panel layout: Balance Sheet (left) + Income Statement (right)
- Account titles that Drake auto-maps to 1065 form lines

Also generates a companion K-1 Summary workbook with per-partner details.
"""
import xlwt
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.drake.trial_balance import (
    InvestmentFundData,
    PartnerInfo,
    build_trial_balance,
    BalanceSheetEntry,
    IncomeStatementEntry,
)


# ─── Style Definitions ────────────────────────────────────────────

def _styles():
    """Create Excel styles matching Drake template appearance."""
    header = xlwt.XFStyle()
    header.font = xlwt.Font()
    header.font.bold = True
    header.font.height = 240  # 12pt
    
    section = xlwt.XFStyle()
    section.font = xlwt.Font()
    section.font.bold = True
    section.font.underline = True
    
    currency = xlwt.XFStyle()
    currency.num_format_str = '#,##0'
    
    currency_bold = xlwt.XFStyle()
    currency_bold.num_format_str = '#,##0'
    currency_bold.font = xlwt.Font()
    currency_bold.font.bold = True
    
    label = xlwt.XFStyle()
    
    indent = xlwt.XFStyle()
    indent.alignment = xlwt.Alignment()
    indent.alignment.inde = 1
    
    return {
        'header': header,
        'section': section,
        'currency': currency,
        'currency_bold': currency_bold,
        'label': label,
        'indent': indent,
    }


def generate_drake_workbook(
    fund: InvestmentFundData,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a Drake Trial Balance Import .xls file for a 1065 return.
    
    Args:
        fund: InvestmentFundData with all financial information
        output_path: Where to save the file. If None, auto-generates path.
    
    Returns:
        Path to the generated .xls file
    """
    tb = build_trial_balance(fund)
    
    wb = xlwt.Workbook()
    ws = wb.add_sheet(f'1065 - {fund.entity_name[:20]}')
    styles = _styles()
    
    # Column widths (matching Drake template)
    ws.col(0).width = 256 * 2   # A - spacer
    ws.col(1).width = 256 * 35  # B - Account titles
    ws.col(2).width = 256 * 15  # C - Debit
    ws.col(3).width = 256 * 15  # D - Credit
    ws.col(4).width = 256 * 15  # E - Total
    ws.col(5).width = 256 * 2   # F - spacer
    ws.col(6).width = 256 * 2   # G - spacer
    ws.col(7).width = 256 * 35  # H - Income account titles
    ws.col(8).width = 256 * 15  # I - Amount
    ws.col(9).width = 256 * 15  # J - Total
    
    row = 0
    
    # ─── Header ────────────────────────────────────────────
    ws.write(row, 1, f'{fund.entity_name} (Partnership)', styles['header'])
    row += 2
    
    # ─── LEFT SIDE: Balance Sheet ──────────────────────────
    ws.write(row, 1, 'Balance Sheet', styles['section'])
    ws.write(row, 7, 'Income Statement', styles['section'])
    row += 1
    
    # Current Assets
    ws.write(row, 1, 'Current Assets', styles['section'])
    row += 1
    
    bs_start_row = row
    total_debits = 0
    total_credits = 0
    
    # Write balance sheet entries
    asset_entries = [e for e in tb['balance_sheet'] if e.debit > 0 and e.account_title not in [
        'Accounts payable', 'Notes payable', 'Other long-term liabilities'
    ]]
    liability_entries = [e for e in tb['balance_sheet'] if e.credit > 0 or e.account_title in [
        'Accounts payable', 'Notes payable', 'Other long-term liabilities'
    ]]
    
    # Assets
    for entry in asset_entries:
        ws.write(row, 1, entry.account_title, styles['label'])
        if entry.debit:
            ws.write(row, 2, entry.debit, styles['currency'])
            total_debits += entry.debit
        if entry.credit:
            ws.write(row, 3, entry.credit, styles['currency'])
            total_credits += entry.credit
        row += 1
    
    row += 1
    ws.write(row, 1, 'Total Assets', styles['section'])
    ws.write(row, 4, total_debits - total_credits, styles['currency_bold'])
    total_assets = total_debits - total_credits
    row += 2
    
    # Liabilities
    ws.write(row, 1, 'Current Liabilities', styles['section'])
    row += 1
    
    total_liab = 0
    for entry in liability_entries:
        ws.write(row, 1, entry.account_title, styles['label'])
        ws.write(row, 3, entry.credit, styles['currency'])
        total_liab += entry.credit
        row += 1
    
    row += 1
    ws.write(row, 1, 'Total Liabilities', styles['section'])
    ws.write(row, 4, total_liab, styles['currency_bold'])
    row += 2
    
    # Partners' Equity
    ws.write(row, 1, "Partners' Equity", styles['section'])
    row += 1
    
    partners_capital_total = sum(
        p.capital_beginning + p.capital_contributions for p in fund.partners
    ) if fund.partners else 0
    
    ws.write(row, 1, "Partners' capital", styles['label'])
    ws.write(row, 2, partners_capital_total, styles['currency'])
    row += 1
    
    ws.write(row, 1, "Current year income", styles['label'])
    ws.write(row, 2, tb['net_income'], styles['currency'])
    row += 1
    
    if fund.distributions_to_partners:
        ws.write(row, 1, "Distributions", styles['label'])
        ws.write(row, 3, fund.distributions_to_partners, styles['currency'])
        row += 1
    
    total_equity = partners_capital_total + tb['net_income'] - fund.distributions_to_partners
    row += 1
    ws.write(row, 1, 'Total Equity', styles['section'])
    ws.write(row, 4, total_equity, styles['currency_bold'])
    row += 2
    
    ws.write(row, 1, "Total Liabilities and Partners' Equity", styles['section'])
    ws.write(row, 4, total_liab + total_equity, styles['currency_bold'])
    
    # ─── RIGHT SIDE: Income Statement ──────────────────────
    is_row = bs_start_row
    
    # Income items
    income_entries = [e for e in tb['income_statement'] if not any(
        kw in e.account_title.lower() for kw in ['fees', 'deduction', 'expense', 'accounting', 'legal']
    )]
    expense_entries = [e for e in tb['income_statement'] if any(
        kw in e.account_title.lower() for kw in ['fees', 'deduction', 'expense', 'accounting', 'legal']
    )]
    
    # Separately Stated Items (these go on K-1, not page 1)
    ws.write(is_row, 7, 'Separately Stated Items', styles['section'])
    is_row += 1
    
    for entry in income_entries:
        ws.write(is_row, 7, entry.account_title, styles['label'])
        ws.write(is_row, 9, entry.amount, styles['currency'])
        is_row += 1
    
    is_row += 1
    ws.write(is_row, 7, 'Expenses', styles['section'])
    is_row += 1
    
    for entry in expense_entries:
        ws.write(is_row, 7, entry.account_title, styles['label'])
        ws.write(is_row, 8, entry.amount, styles['currency'])
        is_row += 1
    
    is_row += 1
    ws.write(is_row, 7, 'Total Expenses', styles['section'])
    ws.write(is_row, 9, tb['total_expenses'], styles['currency_bold'])
    
    is_row += 1
    ws.write(is_row, 7, 'Net Income', styles['section'])
    ws.write(is_row, 9, tb['net_income'], styles['currency_bold'])
    
    # Save
    if not output_path:
        safe_name = fund.entity_name.replace(' ', '_').replace('/', '-')[:30]
        output_path = f"output/{safe_name}_1065_TB_{fund.tax_year}.xls"
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    
    return output_path


def generate_k1_workbook(
    fund: InvestmentFundData,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a K-1 summary workbook with per-partner allocation details.
    This is a companion to the trial balance — the CPA uses this to
    verify K-1 amounts and enter partner-level data in Drake.
    """
    tb = build_trial_balance(fund)
    
    wb = xlwt.Workbook()
    styles = _styles()
    
    # ─── Summary Sheet ─────────────────────────────────────
    summary = wb.add_sheet('K-1 Summary')
    summary.col(0).width = 256 * 5
    summary.col(1).width = 256 * 30
    summary.col(2).width = 256 * 15
    summary.col(3).width = 256 * 15
    summary.col(4).width = 256 * 15
    summary.col(5).width = 256 * 15
    summary.col(6).width = 256 * 15
    summary.col(7).width = 256 * 15
    summary.col(8).width = 256 * 15
    
    row = 0
    summary.write(row, 1, f'{fund.entity_name} — Schedule K-1 Allocations', styles['header'])
    summary.write(row + 1, 1, f'Tax Year {fund.tax_year}')
    summary.write(row + 2, 1, f'EIN: {fund.ein}')
    summary.write(row + 3, 1, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    row = 5
    
    # Column headers
    headers = [
        '', 'Partner Name', 'Ownership %', 'LT Cap Gain',
        'ST Cap Gain', 'Ordinary Inc', 'Distributions',
        'Capital Beg', 'Capital End'
    ]
    for col, h in enumerate(headers):
        summary.write(row, col, h, styles['section'])
    row += 1
    
    # Partner rows
    for i, alloc in enumerate(tb['partner_allocations'], 1):
        summary.write(row, 0, i, styles['label'])
        summary.write(row, 1, alloc['partner_name'], styles['label'])
        summary.write(row, 2, alloc['ownership_pct'], styles['currency'])
        summary.write(row, 3, alloc['net_lt_capital_gain'], styles['currency'])
        summary.write(row, 4, alloc['net_st_capital_gain'], styles['currency'])
        summary.write(row, 5, alloc['ordinary_income'], styles['currency'])
        summary.write(row, 6, alloc['distributions'], styles['currency'])
        summary.write(row, 7, alloc['capital_beginning'], styles['currency'])
        summary.write(row, 8, alloc['capital_ending'], styles['currency'])
        row += 1
    
    # Totals row
    row += 1
    summary.write(row, 1, 'TOTALS', styles['section'])
    for col_idx, key in [(3, 'net_lt_capital_gain'), (4, 'net_st_capital_gain'),
                          (5, 'ordinary_income'), (6, 'distributions')]:
        total = sum(a[key] for a in tb['partner_allocations'])
        summary.write(row, col_idx, total, styles['currency_bold'])
    
    # ─── Individual K-1 Sheets ─────────────────────────────
    for alloc in tb['partner_allocations']:
        safe_name = alloc['partner_name'][:25].replace('/', '-')
        sheet = wb.add_sheet(safe_name)
        sheet.col(0).width = 256 * 5
        sheet.col(1).width = 256 * 40
        sheet.col(2).width = 256 * 20
        
        r = 0
        sheet.write(r, 1, f'Schedule K-1 (Form 1065) — {fund.tax_year}', styles['header'])
        r += 1
        sheet.write(r, 1, f'Partnership: {fund.entity_name}')
        r += 1
        sheet.write(r, 1, f'EIN: {fund.ein}')
        r += 2
        
        sheet.write(r, 1, 'Part II — Information About the Partner', styles['section'])
        r += 1
        sheet.write(r, 1, f"Partner Name: {alloc['partner_name']}")
        r += 1
        sheet.write(r, 1, f"TIN: {alloc.get('tin', 'TBD')}")
        r += 1
        sheet.write(r, 1, f"Ownership: {alloc['ownership_pct']}%")
        r += 1
        sheet.write(r, 1, f"Profit/Loss: {alloc['profit_loss_pct']}%")
        r += 2
        
        sheet.write(r, 1, 'Part III — Partner\'s Share of Income', styles['section'])
        r += 1
        
        k1_lines = [
            ('1', 'Ordinary business income (loss)', alloc['ordinary_income']),
            ('8', 'Net short-term capital gain (loss)', alloc['net_st_capital_gain']),
            ('9a', 'Net long-term capital gain (loss)', alloc['net_lt_capital_gain']),
            ('19', 'Distributions', alloc['distributions']),
        ]
        
        for line_no, desc, amount in k1_lines:
            sheet.write(r, 0, line_no, styles['label'])
            sheet.write(r, 1, desc, styles['label'])
            sheet.write(r, 2, amount, styles['currency'])
            r += 1
        
        r += 2
        sheet.write(r, 1, "Part II, Item L — Partner's Capital Account", styles['section'])
        r += 1
        
        cap_lines = [
            ('Beginning capital account', alloc['capital_beginning']),
            ('Capital contributed during year', alloc['capital_contributions']),
            ('Current year increase (decrease)', alloc['capital_share_of_income']),
            ('Withdrawals & distributions', -(alloc['capital_withdrawals'] + alloc['distributions'])),
            ('Ending capital account', alloc['capital_ending']),
        ]
        
        for desc, amount in cap_lines:
            sheet.write(r, 1, desc, styles['label'])
            sheet.write(r, 2, amount, styles['currency'])
            r += 1
    
    # Save
    if not output_path:
        safe_name = fund.entity_name.replace(' ', '_').replace('/', '-')[:30]
        output_path = f"output/{safe_name}_K1_Summary_{fund.tax_year}.xls"
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    
    return output_path


def generate_full_package(
    fund: InvestmentFundData,
    output_dir: str = "output",
) -> dict:
    """
    Generate the complete Drake import package:
    1. Trial Balance Import .xls (for Drake import)
    2. K-1 Summary .xls (for CPA review)
    3. Extension form data (Form 7004)
    
    Returns dict with file paths.
    """
    safe_name = fund.entity_name.replace(' ', '_').replace('/', '-')[:30]
    
    tb_path = generate_drake_workbook(
        fund, f"{output_dir}/{safe_name}_1065_TB_{fund.tax_year}.xls"
    )
    
    k1_path = generate_k1_workbook(
        fund, f"{output_dir}/{safe_name}_K1_Summary_{fund.tax_year}.xls"
    )
    
    return {
        "trial_balance": tb_path,
        "k1_summary": k1_path,
        "entity_name": fund.entity_name,
        "tax_year": fund.tax_year,
        "partner_count": len(fund.partners),
        "net_income": build_trial_balance(fund)['net_income'],
    }
