"""Data models for the fashion e-commerce discount system."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class DiscountType(str, Enum):
    """Canonical labels for each discount tier."""

    BRAND = "brand"
    CATEGORY = "category"
    VOUCHER = "voucher"
    BANK = "bank"


class CardType(str, Enum):
    """Supported card types for bank offers."""

    CREDIT = "credit"
    DEBIT = "debit"


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    brand: str
    category: str
    mrp: Decimal

    def __post_init__(self) -> None:
        if self.mrp <= 0:
            raise ValueError(f"MRP must be positive, got {self.mrp}")


@dataclass
class CartItem:
    product: Product
    quantity: int = 1

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError(f"Quantity must be at least 1, got {self.quantity}")

    @property
    def subtotal(self) -> Decimal:
        return self.product.mrp * self.quantity


@dataclass(frozen=True)
class PaymentInfo:
    bank: str
    card_type: CardType


@dataclass(frozen=True)
class DiscountBreakdown:
    """Audit record for a single discount step applied to a product."""

    discount_type: DiscountType
    description: str
    percentage: Decimal
    amount: Decimal
    price_before: Decimal
    price_after: Decimal


@dataclass
class DiscountedPrice:
    """Final pricing result for one cart item, with a full breakdown."""

    product_name: str
    quantity: int
    original_price: Decimal
    final_price: Decimal
    total_discount: Decimal
    total_discount_percentage: Decimal
    applied_discounts: list[DiscountBreakdown] = field(default_factory=list)
