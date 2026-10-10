from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from .ingestion.models import Customer, Expense, Invoice


# Reuse the input contracts without accepting a client-supplied organization ID.
def public_input(name, model):
    return create_model(
        name,
        __config__=ConfigDict(extra="forbid", str_strip_whitespace=True),
        **{
            k: (v.annotation, v)
            for k, v in model.model_fields.items()
            if k != "organization_id"
        },
    )


CustomerInput = public_input("CustomerInput", Customer)
InvoiceInput = public_input("InvoiceInput", Invoice)
ExpenseInput = public_input("ExpenseInput", Expense)


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class GrantInput(BaseModel):
    customer_ids: list[str] = Field(max_length=200)


class Terms(BaseModel):
    model_config = ConfigDict(extra="forbid")
    effective_from: date
    effective_to: date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    billing_frequency: Literal["monthly"] = "monthly"
    monthly_rate: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    monthly_discount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    source_page: int = Field(ge=1)

    @model_validator(mode="after")
    def valid(self):
        if self.effective_to < self.effective_from:
            raise ValueError("Effective end date must be on or after start date")
        if self.monthly_discount > self.monthly_rate:
            raise ValueError("Monthly discount cannot exceed rate")
        return self
