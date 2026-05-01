from datetime import datetime
from processing.schemas import NormalizedTransaction

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

def normalize_transaction(raw: dict) -> NormalizedTransaction:
    source = raw.get("source_system", "").lower()
    review_reasons: list[str] = []

    # Extract fields based on source system
    if source == "quickbooks":
        tx_id = raw.get("tx_ref", "")
        raw_date = raw.get("date", "")
        description = raw.get("memo", "")
        raw_amount = raw.get("amount")
    elif source == "xero":
        tx_id = raw.get("id", "")
        raw_date = raw.get("transactionDate", "")
        description = raw.get("description", "")
        raw_amount = raw.get("value")
    else:
        # Unknown source — try to process, but flag it for review
        tx_id = raw.get("tx_ref") or raw.get("id") or ""
        raw_date = raw.get("date") or raw.get("transactionDate") or ""
        description = raw.get("memo") or raw.get("description") or ""
        raw_amount = raw.get("amount") or raw.get("value")
        review_reasons.append(f"Unknown source system: '{raw.get('source_system')}'")

    # Parse date
    try:
        if source == "quickbooks":
            date = parse_quickbooks_date(raw_date)
        elif source == "xero":
            date = parse_xero_date(raw_date)
        else:
            try:
                date = parse_quickbooks_date(raw_date)
            except ValueError:
                date = parse_xero_date(raw_date)
    except (ValueError, TypeError):
        date = raw_date  
        review_reasons.append(f"Could not parse date: '{raw_date}'")

    # Parse amount
    amount, amount_error = parse_amount(raw_amount)
    if amount_error:
        review_reasons.append(amount_error)

    # Check for empty description 
    if not description or not description.strip():
        description = ""
        review_reasons.append("Description is empty")

    return NormalizedTransaction(
        id=tx_id,
        date=date,
        description=description,
        amount=amount,
        currency=DEFAULT_CURRENCY,
        category=None,  
        needs_review=len(review_reasons) > 0,
        review_reasons=review_reasons,
    )
