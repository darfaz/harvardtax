from collections import defaultdict
from app.mapping.tax_lines import QBO_SUBTYPE_TO_1065


class MappingResult:
    def __init__(self):
        self.lines: dict[str, float] = defaultdict(float)
        self.line_details: dict[str, list[dict]] = defaultdict(list)
        self.unmapped: list[dict] = []
    
    def add(self, line: str, amount: float, account_name: str, subtype: str):
        self.lines[line] += amount
        self.line_details[line].append({
            "account_name": account_name,
            "subtype": subtype,
            "amount": amount,
        })
    
    def add_unmapped(self, account: dict):
        self.unmapped.append(account)
    
    def to_dict(self) -> dict:
        return {
            "lines": dict(self.lines),
            "line_details": {k: v for k, v in self.line_details.items()},
            "unmapped_accounts": self.unmapped,
        }


def map_accounts_to_1065(
    accounts: list[dict],
    overrides: dict[str, str] | None = None,
) -> MappingResult:
    result = MappingResult()
    overrides = overrides or {}
    
    for account in accounts:
        account_id = account.get("Id", "")
        name = account.get("Name", "")
        subtype = account.get("AccountSubType", "")
        amount = float(account.get("Balance", 0) or account.get("amount", 0))
        
        if amount == 0:
            continue
        
        if account_id in overrides:
            line = overrides[account_id]
            result.add(line, amount, name, subtype)
            continue
        
        mapping = QBO_SUBTYPE_TO_1065.get(subtype)
        if mapping:
            line, _desc = mapping
            result.add(line, amount, name, subtype)
        else:
            result.add_unmapped({
                "id": account_id,
                "name": name,
                "subtype": subtype,
                "type": account.get("AccountType", ""),
                "amount": amount,
            })
    
    return result


def calculate_1065_totals(result: MappingResult) -> dict:
    lines = result.lines
    cogs = sum(lines.get(k, 0) for k in ["2-purchases", "2-labor", "2-other"])
    lines["2"] = cogs
    lines["3"] = lines.get("1a", 0) - lines.get("1b", 0) - cogs
    lines["8"] = sum(lines.get(str(i), 0) for i in range(3, 8))
    deduction_lines = [9, 10, 11, 12, 13, 14, 15]
    lines["21"] = sum(lines.get(str(i), 0) for i in deduction_lines)
    lines["21"] += lines.get("16a", 0) + lines.get("17", 0)
    lines["21"] += lines.get("18", 0) + lines.get("19", 0) + lines.get("20", 0)
    lines["22"] = lines.get("8", 0) - lines.get("21", 0)
    return dict(lines)
