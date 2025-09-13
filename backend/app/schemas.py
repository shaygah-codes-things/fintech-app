from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal, ROUND_HALF_UP

CURRENCY_WHITELIST = {"USD", "EUR", "GBP"}


def _quantize_money(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ErrorBody(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None


class CreatePayoutRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"))
    currency: str

    @field_validator("currency")
    def currency_must_be_allowed(cls, v: str) -> str:
        v = v.upper()
        if v not in CURRENCY_WHITELIST:
            raise ValueError(f"unsupported currency: {v}")
        return v

    @field_validator("amount")
    def amount_must_be_quantized(cls, v: Decimal) -> Decimal:
        return _quantize_money(v)


class PayoutOut(BaseModel):
    id: int
    amount: str
    currency: str
    status: str


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    page: int
    limit: int
    total: int
    items: List[T]
