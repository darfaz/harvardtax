import pytest
from app.extraction.agreement_parser import EXTRACTION_PROMPT


def test_extraction_prompt_requests_json():
    assert "JSON" in EXTRACTION_PROMPT
    assert "partners" in EXTRACTION_PROMPT
    assert "ownership_pct" in EXTRACTION_PROMPT
    assert "allocation_rules" in EXTRACTION_PROMPT


def test_extraction_prompt_covers_key_fields():
    required_fields = [
        "entity_type", "state_of_formation", "profit_sharing_pct",
        "loss_sharing_pct", "capital_contribution", "is_managing",
        "preferred_return", "carried_interest", "tax_matters_partner",
    ]
    for field in required_fields:
        assert field in EXTRACTION_PROMPT, f"Prompt missing field: {field}"
