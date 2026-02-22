"""
Allocates Schedule K amounts to individual partners for K-1 generation.
MVP: Pro-rata allocation based on ownership percentages.
"""
from decimal import Decimal, ROUND_HALF_UP


def allocate_pro_rata(
    schedule_k_totals: dict[str, float],
    partners: list[dict],
) -> list[dict]:
    results = []
    for partner in partners:
        pct = Decimal(str(partner["ownership_pct"])) / Decimal("100")
        allocations = {}
        for k_line, total in schedule_k_totals.items():
            allocated = Decimal(str(total)) * pct
            allocations[k_line] = float(allocated.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        results.append({
            "partner_id": partner["id"],
            "partner_name": partner["name"],
            "allocations": allocations,
        })
    _fix_rounding(results, schedule_k_totals)
    return results


def _fix_rounding(results: list[dict], totals: dict[str, float]):
    if not results:
        return
    for k_line, total in totals.items():
        allocated_sum = sum(r["allocations"].get(k_line, 0) for r in results)
        diff = round(total - allocated_sum, 0)
        if diff != 0:
            results[-1]["allocations"][k_line] = (
                results[-1]["allocations"].get(k_line, 0) + diff
            )
