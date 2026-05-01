"""
dummy_llm.py
------------

This file simulates an LLM categorisation endpoint.
Import and call `categorize_transaction(description)` in your processing layer.

DO NOT modify this file. Your task is to handle whatever it returns — including the bad outputs.
"""

import random
import time
from typing import Optional

__all__ = ["categorize_transaction"]

# These are the only valid categories your normalisation schema should accept.
VALID_CATEGORIES = ["SOFTWARE", "MEALS", "TRAVEL", "UTILITIES", "PAYROLL"]


def categorize_transaction(description: str) -> Optional[str]:
    """
    Simulates an LLM categorising a financial transaction description.

    Args:
        description: A plain-text transaction description (e.g. "Delta Airlines - YYZ to SFO")

    Returns:
        A category string — but not always a valid or useful one.
        Possible return values:
            - A valid category from VALID_CATEGORIES             (~65% of the time)
            - None  (simulating a failed or timed-out API call)  (~15% of the time)
            - A hallucinated string that isn't in VALID_CATEGORIES (~20% of the time)
    """
    # This simulates real API latency
    time.sleep(random.uniform(0.05, 0.2))

    outcomes = [
        *VALID_CATEGORIES,               # 5 valid options
        None,                            # null / failure
        None,                            # null / failure (weighted up)
        "Super Secret Expense",          # hallucination
        "Miscellaneous Operations Cost", # hallucination
        "Unknown Financial Activity",    # hallucination
    ]

    weights = [
        0.15, 0.15, 0.15, 0.10, 0.10,  # valid categories
        0.10, 0.05,                      # nulls
        0.07, 0.07, 0.06,               # hallucinations
    ]

    return random.choices(outcomes, weights=weights, k=1)[0]