from pydantic import BaseModel
from typing import Optional
from enum import Enum


# Only valid categories the LLM should return — Given (dummy_llm.py)
class Category(str, Enum):
    SOFTWARE = "SOFTWARE"
    MEALS = "MEALS"
    TRAVEL = "TRAVEL"
    UTILITIES = "UTILITIES"
    PAYROLL = "PAYROLL"


class NormalizedTransaction(BaseModel):
    id: str                              # original ref from source system (e.g. "QB-99381A" or "X-10029")
    date: str                            # ISO format: YYYY-MM-DD
    description: str                     # what the transaction is about
    amount: Optional[float]              # null if the source had garbage like "TBD" or "PENDING"
    currency: str                        # default "GBP" 
    category: Optional[str]              # the LLM's output, or None if it failed
    needs_review: bool                   # True if something is off with this transaction
    review_reasons: list[str]            # list of reasons why it needs human review (e.g. ["LLM failed to categorise", "Amount is null"])


class ProcessingResult(BaseModel):
    summary: dict                        # counts: total, processed, flagged
    transactions: list[NormalizedTransaction]
