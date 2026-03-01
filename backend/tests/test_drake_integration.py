"""
Tests for Drake Trial Balance Import generator.
Uses realistic data based on The Garage Syndicate fund structure.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.drake.trial_balance import (
    InvestmentFundData,
    PartnerInfo,
    build_trial_balance,
)
from app.drake.excel_generator import (
    generate_drake_workbook,
    generate_k1_workbook,
    generate_full_package,
)


def _make_scale_fund() -> InvestmentFundData:
    """
    Scale series — based on transcript:
    - ~22 investors, collected ~$300K
    - Invested in underlying SPV (AnderLine)
    - Meta acquired underlying → partial exit 2025
    - ~$250K distributed back (cash)
    - Still hold stock in acquiring company
    """
    partners = []
    # Create 22 sample investors with varying amounts
    investments = [
        ("Investor A", 25000), ("Investor B", 20000), ("Investor C", 15000),
        ("Investor D", 15000), ("Investor E", 12000), ("Investor F", 12000),
        ("Investor G", 10000), ("Investor H", 10000), ("Investor I", 10000),
        ("Investor J", 10000), ("Investor K", 10000), ("Investor L", 10000),
        ("Investor M", 10000), ("Investor N", 10000), ("Investor O", 10000),
        ("Investor P", 10000), ("Investor Q", 10000), ("Investor R", 10000),
        ("Investor S", 10000), ("Investor T", 10000), ("Investor U", 25000),
        ("Investor V", 16000),
    ]
    total_raised = sum(amt for _, amt in investments)
    
    for name, amt in investments:
        pct = round(amt / total_raised * 100, 4)
        # Each investor got proportional distribution
        dist = round(amt / total_raised * 250000)
        partners.append(PartnerInfo(
            id=name.lower().replace(' ', '_'),
            name=name,
            ownership_pct=pct,
            capital_beginning=amt,  # contributed in 2024
            capital_contributions=0,  # no new contributions in 2025
            capital_withdrawals=0,
            profit_pct=pct,
            loss_pct=pct,
        ))
    
    return InvestmentFundData(
        entity_name="TGS Scale Series LLC",
        ein="XX-XXXXXXX",
        tax_year=2025,
        date_formed="2024-04-01",
        state="DE",
        # Balance sheet
        cash=50000,  # remaining cash after distributions
        investments_at_cost=0,  # original investment was $300K
        # Exit: Meta acquisition — received $250K cash + stock worth ~$100K
        exit_proceeds_cash=250000,
        exit_proceeds_stock=100000,  # stock in acquiring company still held
        exit_cost_basis=300000,
        # Capital gains: ($250K + $100K) - $300K = $50K gain
        capital_gains_long=50000,
        # Distributions
        distributions_to_partners=250000,
        # Expenses
        management_fees=5000,
        admin_fees=2000,  # Carta platform fees
        partners=partners,
    )


def _make_carbon_six_fund() -> InvestmentFundData:
    """
    Carbon Six series — based on transcript:
    - ~26 investors, 2 closings
    - Invested ~$600K ($400K + $200K)
    - SAFE converted to equity
    - Partial exit in 2025
    """
    partners = []
    investments = [
        ("Investor A", 50000), ("Investor B", 40000), ("Investor C", 35000),
        ("Investor D", 30000), ("Investor E", 25000), ("Investor F", 25000),
        ("Investor G", 25000), ("Investor H", 20000), ("Investor I", 20000),
        ("Investor J", 20000), ("Investor K", 20000), ("Investor L", 20000),
        ("Investor M", 15000), ("Investor N", 15000), ("Investor O", 15000),
        ("Investor P", 15000), ("Investor Q", 15000), ("Investor R", 15000),
        ("Investor S", 10000), ("Investor T", 10000), ("Investor U", 10000),
        ("Investor V", 10000), ("Investor W", 10000), ("Investor X", 10000),
        ("Investor Y", 25000), ("Investor Z", 25000),
    ]
    total_raised = sum(amt for _, amt in investments)
    
    for name, amt in investments:
        pct = round(amt / total_raised * 100, 4)
        partners.append(PartnerInfo(
            id=name.lower().replace(' ', '_'),
            name=name,
            ownership_pct=pct,
            capital_beginning=amt,
            capital_contributions=0,
            capital_withdrawals=0,
            profit_pct=pct,
            loss_pct=pct,
        ))
    
    return InvestmentFundData(
        entity_name="TGS Carbon Six Series LLC",
        ein="XX-XXXXXXX",
        tax_year=2025,
        date_formed="2022-06-01",
        state="DE",
        cash=100000,
        investments_at_cost=250000,  # remaining investment after partial exit
        # Partial exit — stock + cash deal, ~$1M equivalent
        exit_proceeds_cash=400000,
        exit_proceeds_stock=0,  # all cash in this case
        exit_cost_basis=350000,  # portion of original $600K
        capital_gains_long=50000,
        distributions_to_partners=400000,
        management_fees=8000,
        legal_fees=3000,
        admin_fees=4000,
        partners=partners,
    )


class TestTrialBalance:
    """Test the trial balance data builder."""
    
    def test_build_scale_fund(self):
        fund = _make_scale_fund()
        tb = build_trial_balance(fund)
        
        assert tb['entity_name'] == "TGS Scale Series LLC"
        assert tb['tax_year'] == 2025
        assert len(tb['partner_allocations']) == 22
        assert tb['net_income'] != 0
    
    def test_build_carbon_six_fund(self):
        fund = _make_carbon_six_fund()
        tb = build_trial_balance(fund)
        
        assert tb['entity_name'] == "TGS Carbon Six Series LLC"
        assert len(tb['partner_allocations']) == 26
    
    def test_partner_allocations_sum_correctly(self):
        fund = _make_scale_fund()
        tb = build_trial_balance(fund)
        
        # All partner ownership should sum to ~100%
        total_pct = sum(a['ownership_pct'] for a in tb['partner_allocations'])
        assert 99.5 < total_pct <= 100.1
        
        # Distributions should sum to total
        total_dist = sum(a['distributions'] for a in tb['partner_allocations'])
        assert abs(total_dist - fund.distributions_to_partners) <= len(fund.partners)  # rounding
    
    def test_capital_accounts_balance(self):
        fund = _make_scale_fund()
        tb = build_trial_balance(fund)
        
        for alloc in tb['partner_allocations']:
            expected_ending = (
                alloc['capital_beginning']
                + alloc['capital_contributions']
                + alloc['capital_share_of_income']
                - alloc['capital_withdrawals']
                - alloc['distributions']
            )
            assert alloc['capital_ending'] == expected_ending, (
                f"Capital account doesn't balance for {alloc['partner_name']}"
            )
    
    def test_balance_sheet_entries_present(self):
        fund = _make_scale_fund()
        tb = build_trial_balance(fund)
        
        titles = [e.account_title for e in tb['balance_sheet']]
        assert 'Cash' in titles
        assert 'Other investments' in titles  # stock holding
    
    def test_income_statement_has_gains(self):
        fund = _make_scale_fund()
        tb = build_trial_balance(fund)
        
        income_titles = [e.account_title for e in tb['income_statement']]
        assert any('capital gain' in t.lower() for t in income_titles)


class TestExcelGeneration:
    """Test actual Excel file generation."""
    
    def test_generate_scale_trial_balance(self, tmp_path):
        fund = _make_scale_fund()
        path = generate_drake_workbook(fund, str(tmp_path / "scale_tb.xls"))
        
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        print(f"Generated: {path} ({os.path.getsize(path)} bytes)")
    
    def test_generate_scale_k1_workbook(self, tmp_path):
        fund = _make_scale_fund()
        path = generate_k1_workbook(fund, str(tmp_path / "scale_k1.xls"))
        
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        print(f"Generated: {path} ({os.path.getsize(path)} bytes)")
    
    def test_generate_carbon_six_full_package(self, tmp_path):
        fund = _make_carbon_six_fund()
        result = generate_full_package(fund, str(tmp_path))
        
        assert os.path.exists(result['trial_balance'])
        assert os.path.exists(result['k1_summary'])
        assert result['partner_count'] == 26
        print(f"Package: {result}")
    
    def test_generate_full_package_scale(self, tmp_path):
        fund = _make_scale_fund()
        result = generate_full_package(fund, str(tmp_path))
        
        assert result['partner_count'] == 22
        assert result['tax_year'] == 2025
    
    def test_k1_workbook_has_individual_sheets(self, tmp_path):
        """Each partner should get their own K-1 sheet."""
        fund = _make_scale_fund()
        path = generate_k1_workbook(fund, str(tmp_path / "k1.xls"))
        
        import xlrd
        wb = xlrd.open_workbook(path)
        # Summary sheet + 22 partner sheets = 23
        assert len(wb.sheet_names()) == 23
        assert wb.sheet_names()[0] == 'K-1 Summary'


class TestEdgeCases:
    """Test edge cases and unusual fund structures."""
    
    def test_fund_with_no_exit(self):
        """Fund that just collected capital, no exit yet."""
        fund = InvestmentFundData(
            entity_name="Test Fund No Exit",
            tax_year=2025,
            cash=50000,
            investments_at_cost=250000,
            admin_fees=1000,
            partners=[
                PartnerInfo(id="p1", name="Partner 1", ownership_pct=60,
                           capital_beginning=180000, profit_pct=60, loss_pct=60),
                PartnerInfo(id="p2", name="Partner 2", ownership_pct=40,
                           capital_beginning=120000, profit_pct=40, loss_pct=40),
            ],
        )
        tb = build_trial_balance(fund)
        # Should still generate valid output, just with losses (expenses only)
        assert tb['total_expenses'] == 1000
        assert tb['net_income'] == -1000
    
    def test_fund_with_loss(self):
        """Fund where exit is below cost basis."""
        fund = InvestmentFundData(
            entity_name="Loss Fund",
            tax_year=2025,
            cash=10000,
            exit_proceeds_cash=100000,
            exit_cost_basis=200000,
            capital_gains_long=-100000,
            distributions_to_partners=100000,
            management_fees=5000,
            partners=[
                PartnerInfo(id="p1", name="Partner 1", ownership_pct=50,
                           capital_beginning=100000, profit_pct=50, loss_pct=50),
                PartnerInfo(id="p2", name="Partner 2", ownership_pct=50,
                           capital_beginning=100000, profit_pct=50, loss_pct=50),
            ],
        )
        tb = build_trial_balance(fund)
        assert tb['net_income'] < 0
    
    def test_single_partner(self):
        """Single-member fund (still needs 1065 if LLC)."""
        fund = InvestmentFundData(
            entity_name="Solo Fund",
            tax_year=2025,
            cash=5000,
            capital_gains_long=10000,
            exit_proceeds_cash=10000,
            exit_cost_basis=0,
            partners=[
                PartnerInfo(id="p1", name="Solo Partner", ownership_pct=100,
                           capital_beginning=50000, profit_pct=100, loss_pct=100),
            ],
        )
        tb = build_trial_balance(fund)
        assert len(tb['partner_allocations']) == 1
        assert tb['partner_allocations'][0]['ownership_pct'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
