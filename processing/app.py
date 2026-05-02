from fastapi import FastAPI
from processing.normalizer import normalize_transaction
from processing.categorizer import categorize_and_validate
from processing.schemas import ProcessingResult

app = FastAPI(title="ALFRD Task")

@app.post("/process", response_model=ProcessingResult)
def process_transactions(transactions: list[dict]):
    normalized = []

    for raw in transactions:
        try:
            # Normalize into unified schema
            tx = normalize_transaction(raw)

            # Categorize via LLM and catch bad outputs
            tx = categorize_and_validate(tx)

            normalized.append(tx)

        except Exception as e:
            tx_id = raw.get("tx_ref") or raw.get("id") or "UNKNOWN"
            normalized.append({
                "id": tx_id,
                "date": "",
                "description": str(raw),
                "amount": None,
                "currency": "GBP",
                "category": None,
                "needs_review": True,
                "review_reasons": [f"Failed to process: {str(e)}"],
            })

    # Filter transactions that need human review
    flagged = [
        tx for tx in normalized
        if (tx.needs_review if hasattr(tx, "needs_review") else tx.get("needs_review", False))
    ]

    return ProcessingResult(
        summary={
            "total": len(normalized),
            "processed": len(normalized) - len(flagged),
            "flagged": len(flagged),
        },
        transactions=normalized,
    )
