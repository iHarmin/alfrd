from datetime import datetime

DEFAULT_CURRENCY = "GBP" # Clarified with Sammi Teki that we can use GBP currency code for all transactions

def parse_amount(raw_value) -> tuple[float | None, str | None]:
    if raw_value is None:
        return None, "Amount is null"

    if isinstance(raw_value, (int, float)):
        return float(raw_value), None

    # For amount like "TBD" or "PENDING"
    if isinstance(raw_value, str):
        try:
            return float(raw_value), None
        except ValueError:
            return None, f"Amount is not a number: '{raw_value}'"

    return None, f"Unexpected amount type: {type(raw_value).__name__}"

def parse_quickbooks_date(date_str: str) -> str:
    # QuickBooks uses YYYY-MM-DD 
    parsed = datetime.strptime(date_str, "%Y-%m-%d")
    return parsed.strftime("%Y-%m-%d")


def parse_xero_date(date_str: str) -> str:
    # Xero uses DD/MM/YYYY, converted to ISO format (YYYY-MM-DD)
    parsed = datetime.strptime(date_str, "%d/%m/%Y")
    return parsed.strftime("%Y-%m-%d")

