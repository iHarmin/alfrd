import sys
import os

# Add project root to path for importing dummy_llm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dummy_llm import categorize_transaction, VALID_CATEGORIES
from processing.schemas import NormalizedTransaction


def categorize_and_validate(transaction: NormalizedTransaction) -> NormalizedTransaction:
    # If there's no description, skip the LLM call and flag for review immediately
    if not transaction.description.strip():
        transaction.category = None
        if "Description is empty" not in transaction.review_reasons:
            transaction.review_reasons.append("Cannot categorize: description is empty")
            transaction.needs_review = True
        return transaction

    # Call the dummy LLM categorization function
    result = categorize_transaction(transaction.description)

    return transaction
