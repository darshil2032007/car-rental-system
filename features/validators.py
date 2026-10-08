# Input validation functions using Regular Expressions and Assert statements
import re
from features.exceptions import InvalidPhoneError, InvalidLicenseError


def validate_phone(phone):
    """
    Validates that the phone number contains exactly 10 digits starting with 6-9.
    Raises InvalidPhoneError if format is invalid.
    """
    pattern = r"^[6-9]\d{9}$"
    if not re.match(pattern, str(phone).strip()):
        raise InvalidPhoneError(f"Invalid phone number '{phone}'. It must be a 10-digit number starting with 6, 7, 8, or 9.")
    return True


def validate_email(email):
    """
    Validates general email format using regex.
    Raises ValueError if format is invalid.
    """
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(pattern, str(email).strip()):
        raise ValueError(f"Invalid email address '{email}'.")
    return True


def validate_license(license_no):
    """
    Validates Indian driving license format.
    Example: GJ0120230012345 (2 state letters + 2 RTO digits + 4 year digits + 7 unique digits = 15 characters).
    Raises InvalidLicenseError if format is invalid.
    """
    pattern = r"^[A-Z]{2}\d{2}\d{4}\d{7}$"
    cleaned = str(license_no).strip().upper()
    if not re.match(pattern, cleaned):
        raise InvalidLicenseError(f"Invalid license number '{license_no}'. Format example: GJ0120230012345 (15 characters).")
    return True


def validate_rate(rate_per_day):
    """
    Validates that rate per day is positive using Python assert statement.
    """
    rate = float(rate_per_day)
    assert rate > 0, "Rate per day must be greater than 0."
    return True
