import re
import uuid
from typing import Optional
from django.contrib.auth import get_user_model


def normalize_phone_number(raw_phone: Optional[str]) -> Optional[str]:
    """
    Normalizes a user-supplied phone number into canonical E.164 format.
    
    Supports:
    - 10-digit Indian numbers: "9876543210" -> "+919876543210"
    - Prefixed with +91: "+919876543210" -> "+919876543210"
    - Prefixed with 91: "919876543210" -> "+919876543210"
    - Prefixed with 0: "09876543210" -> "+919876543210"
    - Handles spaces, dashes, dots, parentheses: "+91 98765-43210" -> "+919876543210"
    - General international E.164 numbers (+ followed by 10 to 15 digits).
    
    Returns None if invalid.
    """
    if not raw_phone:
        return None

    cleaned = str(raw_phone).strip()
    # Strip spaces, hyphens, dots, parentheses
    cleaned = re.sub(r"[\s\-\(\)\.]", "", cleaned)

    if not cleaned:
        return None

    # Handle Indian mobile numbers
    # Pattern 1: +91 followed by 10 digits starting with 6, 7, 8, 9
    if re.fullmatch(r"\+91[6-9]\d{9}", cleaned):
        return cleaned

    # Pattern 2: 91 followed by 10 digits starting with 6, 7, 8, 9
    if re.fullmatch(r"91[6-9]\d{9}", cleaned):
        return f"+{cleaned}"

    # Pattern 3: 0 followed by 10 digits starting with 6, 7, 8, 9
    if re.fullmatch(r"0[6-9]\d{9}", cleaned):
        return f"+91{cleaned[1:]}"

    # Pattern 4: 10 digits starting with 6, 7, 8, 9
    if re.fullmatch(r"[6-9]\d{9}", cleaned):
        return f"+91{cleaned}"

    # General international E.164 (e.g. +14155552671)
    if re.fullmatch(r"\+[1-9]\d{9,14}", cleaned):
        return cleaned

    return None


def is_valid_phone_number(raw_phone: Optional[str]) -> bool:
    """Returns True if the raw phone number can be normalized."""
    return normalize_phone_number(raw_phone) is not None


def generate_internal_username(base_name: Optional[str] = "student") -> str:
    """
    Generates a unique internal username that does not expose phone numbers
    or conflict with existing users.
    
    Format: student_<8-char-hex>
    """
    User = get_user_model()
    clean_base = "student"
    if base_name:
        sanitized = re.sub(r"[^a-zA-Z0-9]", "", str(base_name).lower())[:10]
        if sanitized:
            clean_base = sanitized

    for _ in range(50):
        suffix = uuid.uuid4().hex[:8]
        candidate = f"{clean_base}_{suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate

    # Fallback to full uuid hex if collisions occur
    return f"student_{uuid.uuid4().hex[:16]}"
