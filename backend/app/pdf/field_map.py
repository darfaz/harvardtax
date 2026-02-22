"""
Maps 1065 line numbers to IRS PDF form field names.
Field names need to be verified against actual PDF — these are placeholders
based on common IRS PDF naming conventions.
"""

FORM_1065_FIELDS = {
    "entity_name": "topmostSubform[0].Page1[0].Name[0]",
    "ein": "topmostSubform[0].Page1[0].EIN[0]",
    "address_street": "topmostSubform[0].Page1[0].Address[0]",
    "address_city_state_zip": "topmostSubform[0].Page1[0].CityStateZip[0]",
    "1a": "topmostSubform[0].Page1[0].Line1a[0]",
    "1b": "topmostSubform[0].Page1[0].Line1b[0]",
    "1c": "topmostSubform[0].Page1[0].Line1c[0]",
    "2": "topmostSubform[0].Page1[0].Line2[0]",
    "3": "topmostSubform[0].Page1[0].Line3[0]",
    "7": "topmostSubform[0].Page1[0].Line7[0]",
    "8": "topmostSubform[0].Page1[0].Line8[0]",
    "9": "topmostSubform[0].Page1[0].Line9[0]",
    "10": "topmostSubform[0].Page1[0].Line10[0]",
    "11": "topmostSubform[0].Page1[0].Line11[0]",
    "12": "topmostSubform[0].Page1[0].Line12[0]",
    "13": "topmostSubform[0].Page1[0].Line13[0]",
    "14": "topmostSubform[0].Page1[0].Line14[0]",
    "15": "topmostSubform[0].Page1[0].Line15[0]",
    "16a": "topmostSubform[0].Page1[0].Line16a[0]",
    "20": "topmostSubform[0].Page1[0].Line20[0]",
    "21": "topmostSubform[0].Page1[0].Line21[0]",
    "22": "topmostSubform[0].Page1[0].Line22[0]",
}

SCHEDULE_K1_FIELDS = {
    "partnership_name": "topmostSubform[0].Page1[0].PartnershipName[0]",
    "partnership_ein": "topmostSubform[0].Page1[0].PartnershipEIN[0]",
    "partner_name": "topmostSubform[0].Page1[0].PartnerName[0]",
    "partner_ssn": "topmostSubform[0].Page1[0].PartnerSSN[0]",
    "partner_address": "topmostSubform[0].Page1[0].PartnerAddress[0]",
    "partner_type": "topmostSubform[0].Page1[0].PartnerType[0]",
    "profit_pct": "topmostSubform[0].Page1[0].ProfitPct[0]",
    "loss_pct": "topmostSubform[0].Page1[0].LossPct[0]",
    "capital_pct": "topmostSubform[0].Page1[0].CapitalPct[0]",
    "box_1": "topmostSubform[0].Page1[0].Box1[0]",
    "box_2": "topmostSubform[0].Page1[0].Box2[0]",
    "box_4": "topmostSubform[0].Page1[0].Box4[0]",
    "box_5": "topmostSubform[0].Page1[0].Box5[0]",
    "box_6a": "topmostSubform[0].Page1[0].Box6a[0]",
    "box_13": "topmostSubform[0].Page1[0].Box13[0]",
    "box_18": "topmostSubform[0].Page1[0].Box18[0]",
    "box_19": "topmostSubform[0].Page1[0].Box19[0]",
}
