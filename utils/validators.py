import re

def validate_email(email):
    if not email:
        return True # Optional field
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, str(email)) is not None

def validate_sebi_reg_no(reg_no):
    if not reg_no:
        return False
    # Example format: INZ000000000
    pattern = r"^[A-Z0-9]{10,15}$"
    return re.match(pattern, str(reg_no)) is not None

def validate_positive_number(val):
    try:
        if val is None or str(val).strip() == "":
            return False
        return float(val) >= 0
    except ValueError:
        return False
