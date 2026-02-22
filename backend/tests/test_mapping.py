import pytest
from app.mapping.engine import map_accounts_to_1065, calculate_1065_totals, MappingResult
from app.mapping.tax_lines import QBO_SUBTYPE_TO_1065


def test_mapping_table_has_common_subtypes():
    required = [
        "SalesOfProductIncome", "ServiceFeeIncome",
        "PayrollExpenses", "RentOrLeaseOfBuildings",
        "InterestPaid", "Depreciation", "Checking",
        "AccountsReceivable", "AccountsPayable",
    ]
    for subtype in required:
        assert subtype in QBO_SUBTYPE_TO_1065, f"Missing mapping for {subtype}"


def test_map_simple_income():
    accounts = [
        {"Id": "1", "Name": "Sales", "AccountSubType": "ServiceFeeIncome",
         "AccountType": "Income", "Balance": 100000},
    ]
    result = map_accounts_to_1065(accounts)
    assert result.lines["1a"] == 100000
    assert len(result.unmapped) == 0


def test_map_expense_to_line_20():
    accounts = [
        {"Id": "2", "Name": "Advertising", "AccountSubType": "AdvertisingPromotional",
         "AccountType": "Expense", "Balance": 5000},
    ]
    result = map_accounts_to_1065(accounts)
    assert result.lines["20"] == 5000


def test_unmapped_accounts():
    accounts = [
        {"Id": "3", "Name": "Weird Account", "AccountSubType": "UnknownSubType",
         "AccountType": "Expense", "Balance": 1000},
    ]
    result = map_accounts_to_1065(accounts)
    assert len(result.unmapped) == 1
    assert result.unmapped[0]["name"] == "Weird Account"


def test_user_override():
    accounts = [
        {"Id": "4", "Name": "Misc", "AccountSubType": "OtherBusinessExpenses",
         "AccountType": "Expense", "Balance": 2000},
    ]
    overrides = {"4": "13"}
    result = map_accounts_to_1065(accounts, overrides=overrides)
    assert result.lines["13"] == 2000
    assert "20" not in result.lines


def test_zero_balance_skipped():
    accounts = [
        {"Id": "5", "Name": "Empty", "AccountSubType": "Checking",
         "AccountType": "Bank", "Balance": 0},
    ]
    result = map_accounts_to_1065(accounts)
    assert len(result.lines) == 0


def test_calculate_totals():
    result = MappingResult()
    result.lines["1a"] = 500000
    result.lines["1b"] = 5000
    result.lines["2-purchases"] = 100000
    result.lines["2-labor"] = 50000
    result.lines["9"] = 80000
    result.lines["13"] = 24000
    result.lines["14"] = 10000
    result.lines["20"] = 15000
    totals = calculate_1065_totals(result)
    assert totals["2"] == 150000
    assert totals["3"] == 345000
    assert totals["22"] == 345000 - (80000 + 24000 + 10000 + 15000)
