from typing import List, Dict
from pydantic import BaseModel
from enum import Enum
from decimal import Decimal
from datetime import datetime


class Type(str, Enum):
    buy = "buy"
    sell = "sell"
    transfer = "transfer"


class TaxableEvent(BaseModel):
    timestamp: datetime
    asset: str
    type: Type
    asset_amount: Decimal
    aud_amount: Decimal


class SuperTransfer(BaseModel):
    timestamp: datetime
    asset: str
    asset_amount: Decimal


class ParseFileResult(BaseModel):
    filename: str
    parsed: bool

class EventResult(BaseModel):
    profit: Decimal
    amount: Decimal
    asset: str
    buying_rate: Decimal
    selling_rate: Decimal
    buying_timestamp: datetime
    selling_timestamp: datetime
    discount: bool


class Adjustment(BaseModel):
    timestamp: datetime
    type: Type
    asset_amount: Decimal
    aud_amount: Decimal
    comment: str

class UnaccountedForFunds(BaseModel):
    timestamp: datetime
    asset: str
    asset_amount: Decimal

class AnnualSummary(BaseModel):
    year: str
    profit: Decimal
    discounted_profit: Decimal

class RemainingBalance(BaseModel):
    asset: str
    asset_amount: Decimal
    aud_amount: Decimal

class CalculationResult(BaseModel):
    files: List[ParseFileResult] = []
    events: List[EventResult] = []
    unaccounted_for_funds: List[UnaccountedForFunds] = []
    all_total_profit: int = 0
    annual_summaries: List[AnnualSummary] = []
    adjustments: List[Adjustment] = []
    remaining_balances: List[RemainingBalance] = []
