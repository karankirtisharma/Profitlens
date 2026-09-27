"""Initial business import records; no financial aggregate is calculated here."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ImportRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    organization_id: str = Field(min_length=1)


class Customer(ImportRecord):
    customer_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    industry: str = ""


class PeriodRecord(ImportRecord):
    customer_id: str = Field(min_length=1)
    billing_period: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @field_validator("billing_period")
    @classmethod
    def valid_period(cls, value: str) -> str:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError("billing_period must be YYYY-MM")
        # Reject invalid years such as 0000 as well as noncanonical months.
        date.fromisoformat(f"{value}-01")
        return value


class Invoice(PeriodRecord):
    invoice_id: str = Field(min_length=1)
    subtotal: Decimal = Field(ge=0, decimal_places=2)
    discount: Decimal = Field(ge=0, decimal_places=2)
    tax: Decimal = Field(ge=0, decimal_places=2)
    refund: Decimal = Field(ge=0, decimal_places=2)
    total: Decimal = Field(ge=0, decimal_places=2)

    @model_validator(mode="after")
    def check_total(self) -> Invoice:
        if self.discount + self.refund > self.subtotal:
            raise ValueError("discount plus refund cannot exceed subtotal")
        expected = self.subtotal - self.discount + self.tax - self.refund
        if self.total != expected:
            raise ValueError(f"total must equal subtotal - discount + tax - refund ({expected})")
        return self


class Expense(PeriodRecord):
    expense_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    amount: Decimal = Field(ge=0, decimal_places=2)
