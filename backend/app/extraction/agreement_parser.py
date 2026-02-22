"""
AI-powered operating agreement parser using Claude.
Extracts partner info, ownership %, allocation rules from uploaded PDFs.
"""
import json
import anthropic
from app.config import settings

EXTRACTION_PROMPT = """You are a legal document parser specializing in partnership and LLC operating agreements.

Extract the following structured data from this operating agreement. Return ONLY valid JSON.

{
  "entity": {
    "name": "Legal name of the partnership/LLC",
    "entity_type": "LLC | LP | LLP | GP",
    "state_of_formation": "Two-letter state code",
    "date_formed": "YYYY-MM-DD or null",
    "fiscal_year_end": "MM/DD (e.g., 12/31)",
    "business_purpose": "Brief description"
  },
  "partners": [
    {
      "name": "Full legal name",
      "type": "general_partner | limited_partner | member_manager | member",
      "ownership_pct": 25.0,
      "profit_sharing_pct": 25.0,
      "loss_sharing_pct": 25.0,
      "capital_contribution": 100000,
      "is_managing": true,
      "address": "If mentioned, otherwise null"
    }
  ],
  "allocation_rules": {
    "method": "pro_rata | waterfall | custom",
    "description": "Brief description of how profits/losses are allocated",
    "has_preferred_return": false,
    "preferred_return_rate": null,
    "has_carried_interest": false,
    "carried_interest_pct": null,
    "special_allocations": "Description of any special allocation provisions or null"
  },
  "other_provisions": {
    "tax_matters_partner": "Name of TMP/partnership representative",
    "tax_year": "Calendar or fiscal",
    "accounting_method": "Cash or Accrual"
  }
}

Rules:
- Extract percentages as numbers (25.0 not "25%")
- If a field is not found in the document, use null
- If ownership percentages are not explicit but can be inferred (e.g., "equal partners"), calculate them
- Parse dollar amounts as numbers without formatting
- If multiple classes of interest exist, list each partner entry with their specific class noted in the name field
"""


async def parse_operating_agreement(file_content: bytes, filename: str) -> dict:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    import base64
    b64_content = base64.b64encode(file_content).decode()

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": b64_content,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    return json.loads(response_text.strip())
