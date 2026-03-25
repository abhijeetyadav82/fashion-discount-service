"""Discount rule classes — one dataclass per discount type."""

from __future__ import annotations

from dataclasses import dataclass

from models import DiscountType, PaymentInfo, Product


@dataclass(frozen=True)
class BrandDiscount:
    """E.g. 'Min 40% off on PUMA' — applies across all categories."""

    brand: str
    min_discount_pct: float
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.BRAND

    @property
    def description(self) -> str:
        return self.label or f"Min {self.min_discount_pct}% off on {self.brand}"

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        return product.brand.lower() == self.brand.lower()


@dataclass(frozen=True)
class CategoryDiscount:
    """E.g. 'Extra 10% off on T-Shirts' — stacks on top of brand discounts."""

    category: str
    discount_pct: float
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.CATEGORY

    @property
    def description(self) -> str:
        return self.label or f"Extra {self.discount_pct}% off on {self.category}"

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        return product.category.lower() == self.category.lower()


@dataclass(frozen=True)
class VoucherDiscount:
    """E.g. 'SUPER69' for 69% off on any product."""

    code: str
    discount_pct: float
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.VOUCHER

    @property
    def description(self) -> str:
        return self.label or f"Voucher {self.code}: {self.discount_pct}% off"

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        return True


@dataclass(frozen=True)
class BankOffer:
    """E.g. '10% instant discount on ICICI Bank cards'."""

    bank: str
    discount_pct: float
    card_types: tuple[str, ...] = ("credit", "debit")
    label: str = ""

    @property
    def discount_type(self) -> DiscountType:
        return DiscountType.BANK

    @property
    def description(self) -> str:
        return self.label or f"{self.discount_pct}% instant discount on {self.bank} cards"

    def is_applicable(self, product: Product, payment_info: PaymentInfo | None = None) -> bool:
        if payment_info is None:
            return False
        return (
            payment_info.bank.lower() == self.bank.lower()
            and payment_info.card_type.lower() in {ct.lower() for ct in self.card_types}
        )
