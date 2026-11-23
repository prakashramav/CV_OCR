"""Indian Vehicle Registration Format Validator and State Directory.

Reference: Motor Vehicles Act, 1988 & Central Motor Vehicles Rules (CMVR).
Formats:
1. Standard Series: ^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$
   e.g., MH12DE1433, DL01AB1234, TS09UB5678, KA03MN4567
2. Bharat Series (BH): ^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$
   e.g., 22BH1234AA
3. Military (Broad Arrow prefix): ^[0-9]{2}[A-Z][0-9]{5,6}[A-Z]?$
"""

import re
from typing import Dict, Tuple

# Comprehensive mapping of Indian States and Union Territories to RTO two-letter codes
INDIAN_STATE_CODES: Dict[str, str] = {
    "AN": "Andaman and Nicobar Islands",
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CH": "Chandigarh",
    "CG": "Chhattisgarh",
    "DD": "Daman and Diu",
    "DL": "Delhi",
    "DN": "Dadra and Nagar Haveli",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HP": "Himachal Pradesh",
    "HR": "Haryana",
    "JH": "Jharkhand",
    "JK": "Jammu and Kashmir",
    "KA": "Karnataka",
    "KL": "Kerala",
    "LA": "Ladakh",
    "LD": "Lakshadweep",
    "MH": "Maharashtra",
    "ML": "Meghalaya",
    "MN": "Manipur",
    "MP": "Madhya Pradesh",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "PB": "Punjab",
    "PY": "Puducherry",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TR": "Tripura",
    "TS": "Telangana",
    "UK": "Uttarakhand",
    "UA": "Uttarakhand (Former)",
    "UP": "Uttar Pradesh",
    "WB": "West Bengal",
}

# Regex pattern for Standard State-registered Indian plates:
# State (2 letters) + RTO District (1-2 digits) + Series (0-3 letters) + Unique Number (4 digits)
STANDARD_INDIAN_PATTERN = re.compile(r"^([A-Z]{2})([0-9]{1,2})([A-Z]{0,3})([0-9]{4})$")

# Regex pattern for Bharat (BH) Series plates:
# Year (2 digits) + BH + 4 digits + 1-2 letters
BHARAT_SERIES_PATTERN = re.compile(r"^([0-9]{2})BH([0-9]{4})([A-Z]{1,2})$")


def normalize_plate_text(raw_text: str) -> str:
    """Cleans raw OCR output by stripping whitespace, hyphens, and non-alphanumeric characters,

    converting to uppercase.
    """
    if not raw_text:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw_text)
    return cleaned.upper()


def validate_indian_plate(text: str) -> Tuple[bool, str, str]:
    """Validates whether a normalized string matches Indian vehicle registration standards.

    Returns:
        (is_valid: bool, status_label: str, state_name: str)
    """
    normalized = normalize_plate_text(text)
    if not normalized or len(normalized) < 6:
        return False, "INVALID_LENGTH", "Unknown"

    # Check Standard Series
    std_match = STANDARD_INDIAN_PATTERN.match(normalized)
    if std_match:
        state_code = std_match.group(1)
        if state_code in INDIAN_STATE_CODES:
            return True, "VALID_INDIAN", INDIAN_STATE_CODES[state_code]
        else:
            return False, "UNKNOWN_STATE_CODE", "Unknown"

    # Check Bharat (BH) Series
    bh_match = BHARAT_SERIES_PATTERN.match(normalized)
    if bh_match:
        return True, "VALID_BHARAT_SERIES", "All-India Bharat Series"

    # Fallback heuristic: Starts with known state code but non-standard suffix
    if len(normalized) >= 2 and normalized[:2] in INDIAN_STATE_CODES:
        return False, "SUSPICIOUS_PARTIAL", INDIAN_STATE_CODES[normalized[:2]]

    return False, "NON_STANDARD_FORMAT", "Unknown"
