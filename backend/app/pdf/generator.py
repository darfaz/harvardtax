import os
import subprocess
import tempfile
from pathlib import Path
from app.pdf.field_map import FORM_1065_FIELDS, SCHEDULE_K1_FIELDS

TEMPLATE_DIR = Path(__file__).parent / "templates"


def fill_pdf(template_path: str, field_values: dict[str, str], output_path: str):
    fdf_data = generate_fdf(field_values)
    with tempfile.NamedTemporaryFile(suffix=".fdf", delete=False, mode="w") as f:
        f.write(fdf_data)
        fdf_path = f.name
    try:
        subprocess.run([
            "pdftk", template_path,
            "fill_form", fdf_path,
            "output", output_path,
            "flatten",
        ], check=True)
    finally:
        os.unlink(fdf_path)


def generate_fdf(field_values: dict[str, str]) -> str:
    fields = ""
    for name, value in field_values.items():
        value_escaped = str(value).replace("(", "\\(").replace(")", "\\)")
        fields += f"<< /T ({name}) /V ({value_escaped}) >>\n"
    return f"""%FDF-1.2
1 0 obj
<< /FDF << /Fields [
{fields}
] >> >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF"""


def generate_1065(entity: dict, mapped_data: dict[str, float], output_path: str):
    field_values = {}
    field_values[FORM_1065_FIELDS["entity_name"]] = entity.get("name", "")
    field_values[FORM_1065_FIELDS["ein"]] = entity.get("ein", "")
    field_values[FORM_1065_FIELDS["address_street"]] = entity.get("address_street", "")
    city_state_zip = f"{entity.get('address_city', '')}, {entity.get('address_state', '')} {entity.get('address_zip', '')}"
    field_values[FORM_1065_FIELDS["address_city_state_zip"]] = city_state_zip
    for line_num, amount in mapped_data.items():
        if line_num in FORM_1065_FIELDS:
            field_values[FORM_1065_FIELDS[line_num]] = format_amount(amount)
    fill_pdf(str(TEMPLATE_DIR / "f1065.pdf"), field_values, output_path)


def generate_k1(entity: dict, partner: dict, allocations: dict[str, float], output_path: str):
    field_values = {}
    field_values[SCHEDULE_K1_FIELDS["partnership_name"]] = entity.get("name", "")
    field_values[SCHEDULE_K1_FIELDS["partnership_ein"]] = entity.get("ein", "")
    field_values[SCHEDULE_K1_FIELDS["partner_name"]] = partner.get("name", "")
    field_values[SCHEDULE_K1_FIELDS["partner_ssn"]] = partner.get("ssn_ein", "")
    addr = f"{partner.get('address_street', '')}\n{partner.get('address_city', '')}, {partner.get('address_state', '')} {partner.get('address_zip', '')}"
    field_values[SCHEDULE_K1_FIELDS["partner_address"]] = addr
    field_values[SCHEDULE_K1_FIELDS["profit_pct"]] = f"{partner.get('profit_sharing_pct', partner.get('ownership_pct', 0))}%"
    field_values[SCHEDULE_K1_FIELDS["loss_pct"]] = f"{partner.get('loss_sharing_pct', partner.get('ownership_pct', 0))}%"
    field_values[SCHEDULE_K1_FIELDS["capital_pct"]] = f"{partner.get('ownership_pct', 0)}%"
    k1_box_mapping = {
        "K-1": "box_1", "K-2": "box_2", "K-4": "box_4",
        "K-5": "box_5", "K-6a": "box_6a", "K-13a": "box_13",
        "K-18a": "box_18", "K-18c": "box_19",
    }
    for k_line, box in k1_box_mapping.items():
        if k_line in allocations and allocations[k_line] != 0:
            field_values[SCHEDULE_K1_FIELDS[box]] = format_amount(allocations[k_line])
    fill_pdf(str(TEMPLATE_DIR / "f1065sk1.pdf"), field_values, output_path)


def format_amount(amount: float) -> str:
    if amount < 0:
        return f"({abs(int(amount)):,})"
    return f"{int(amount):,}"
