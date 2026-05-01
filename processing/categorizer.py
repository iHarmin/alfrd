import sys
import os

# Add project root to path for importing dummy_llm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dummy_llm import categorize_transaction, VALID_CATEGORIES
from processing.schemas import NormalizedTransaction


def categorize_and_validate(transaction: NormalizedTransaction) -> NormalizedTransaction:
    """
    Running the dummy LLM on the transaction's description, then checking if the result is actually valid or not.

    Three bad outcomes to catch:
    1. LLM returns None (either timeout orfailure)
    2. LLM returns a hallucinated category (given in dummy_llm.py)
    3. Description is empty (Skipping the LLM call and flag for review immediately)
    """
    # If there's no description, skip the LLM call and flag for review immediately
    if not transaction.description.strip():
        transaction.category = None
        if "Description is empty" not in transaction.review_reasons:
            transaction.review_reasons.append("Cannot categorize: description is empty")
            transaction.needs_review = True
        return transaction

    # Call the dummy LLM categorization function
    result = categorize_transaction(transaction.description)

    if result is None:
        # LLM failed or timed out
        transaction.category = None
        transaction.review_reasons.append("LLM returned null: possible timeout or failure")
        transaction.needs_review = True

    elif result not in VALID_CATEGORIES:
        # LLM hallucinates a category that doesn't exist
        transaction.category = None
        transaction.review_reasons.append(
            f"LLM returned invalid category: '{result}'"
        )
        transaction.needs_review = True

    else:
        # Valid category
        transaction.category = result

    return transaction
