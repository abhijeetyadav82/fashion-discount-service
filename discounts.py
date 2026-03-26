"""Discount rule classes implementing the Strategy pattern.

Adding a new discount type means adding one new class here — the
DiscountService stacking logic requires zero changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from models import CardType, DiscountType, PaymentInfo, Product


class DiscountRule(ABC):
    """Abstract base for all discount rules (Strategy interface)."""

    @property
    @abstractmethod
    def discount_type(self) -> DiscountType: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def percentage(self) -> Decimal: ...

    @abstractmethod
    def is_applicable(
        self, product: Product, payment_info: PaymentInfo | None = None
    ) -> bool: ...

    def calculate(self, price: Decimal) -> tuple[Decimal, Decimal]:
        """Return (discount_amount, price_after_discount)."""
        amount = (price * self.percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return amount, price - amount


@dataclass(frozen=True)
class BrandDiscount(DiscountRule):
    """E.g. 'Min 40% off on PUMA' — applies across all categories."""

    brand: str
    min_discount_pct: Decimal
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.BRAND

    @property
    def description(self) -> str:
        return self.label or f"Min {self.min_discount_pct}% off on {self.brand}"

    @property
    def percentage(self) -> Decimal:
        return self.min_discount_pct

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        return product.brand.lower() == self.brand.lower()


@dataclass(frozen=True)
class CategoryDiscount(DiscountRule):
    """E.g. 'Extra 10% off on T-Shirts' — stacks on top of brand discounts."""

    category: str
    discount_pct: Decimal
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.CATEGORY

    @property
    def description(self) -> str:
        return self.label or f"Extra {self.discount_pct}% off on {self.category}"

    @property
    def percentage(self) -> Decimal:
        return self.discount_pct

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        return product.category.lower() == self.category.lower()


@dataclass(frozen=True)
class VoucherDiscount(DiscountRule):
    """E.g. 'SUPER69' for 69% off on any product."""

    code: str
    discount_pct: Decimal
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.VOUCHER

    @property
    def description(self) -> str:
        return self.label or f"Voucher {self.code}: {self.discount_pct}% off"

    @property
    def percentage(self) -> Decimal:
        return self.discount_pct

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        return True


@dataclass(frozen=True)
class BankOffer(DiscountRule):
    """E.g. '10% instant discount on ICICI Bank cards'."""

    bank: str
    discount_pct: Decimal
    card_types: tuple[CardType, ...] = (CardType.CREDIT, CardType.DEBIT)
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.BANK

    @property
    def description(self) -> str:
        return self.label or f"{self.discount_pct}% instant discount on {self.bank} cards"

    @property
    def percentage(self) -> Decimal:
        return self.discount_pct

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        if payment_info is None:
            return False
        return (
            payment_info.bank.lower() == self.bank.lower()
            and payment_info.card_type in self.card_types
        )
