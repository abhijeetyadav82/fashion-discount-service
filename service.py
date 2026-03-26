"""Core discount service — orchestrates discount stacking and calculation."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from discounts import DiscountRule, VoucherDiscount
from models import (
    CartItem,
    DiscountBreakdown,
    DiscountedPrice,
    DiscountType,
    PaymentInfo,
)


class DiscountService:
    """Calculate and apply discounts to a shopping cart.

    Stacking order (each tier reduces the running price before the next):
      1. Brand discounts    — on MRP
      2. Category discounts — on brand-discounted price
      3. Voucher codes      — on further-reduced price
      4. Bank offers        — applied last

    Within each tier the highest-percentage applicable rule wins.
    """

    def __init__(self, discount_rules: list[DiscountRule]) -> None:
        # Single flat list — adding a new DiscountRule subclass requires
        # no change here; it's picked up automatically by discount_type.
        self._rules = discount_rules

    # ── Public API ──────────────────────────────────────────

    def validate_discount_code(self, code: str) -> VoucherDiscount | None:
        """Return the matching VoucherDiscount or None if the code is invalid."""
        if not code or not code.strip():
            return None
        normalised = code.strip().upper()
        for rule in self._rules:
            if isinstance(rule, VoucherDiscount) and rule.code.upper() == normalised:
                return rule
        return None

    def calculate_cart_discounts(
        self,
        cart_items: list[CartItem],
        payment_info: PaymentInfo | None = None,
        voucher_code: str | None = None,
    ) -> list[DiscountedPrice]:
        """Calculate discounts for every item in the cart.

        Raises:
            ValueError: If a voucher code is supplied but not recognised.
        """
        if not cart_items:
            return []

        voucher: VoucherDiscount | None = None
        if voucher_code:
            voucher = self.validate_discount_code(voucher_code)
            if voucher is None:
                raise ValueError(
                    f"Invalid voucher code '{voucher_code}'. "
                    "Please check the code and try again."
                )

        results: list[DiscountedPrice] = []

        for item in cart_items:
            applied: list[DiscountBreakdown] = []
            price = item.product.mrp

            price = self._apply_best(price, item, payment_info, DiscountType.BRAND, applied)
            price = self._apply_best(price, item, payment_info, DiscountType.CATEGORY, applied)
            if voucher:
                price = self._apply_rule(price, voucher, applied)
            price = self._apply_best(price, item, payment_info, DiscountType.BANK, applied)

            total_discount = item.product.mrp - price
            total_pct = (
                (total_discount / item.product.mrp * Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if item.product.mrp > 0
                else Decimal("0")
            )

            results.append(DiscountedPrice(
                product_name=item.product.name,
                quantity=item.quantity,
                original_price=item.product.mrp,
                final_price=price,
                total_discount=total_discount,
                total_discount_percentage=total_pct,
                applied_discounts=applied,
            ))

        return results

    # ── Internals ───────────────────────────────────────────

    def _applicable_rules(
        self, item: CartItem, payment_info: PaymentInfo | None, dtype: DiscountType,
    ) -> list[DiscountRule]:
        return [
            r for r in self._rules
            if r.discount_type == dtype and r.is_applicable(item.product, payment_info)
        ]

    def _apply_best(
        self, price: Decimal, item: CartItem, payment_info: PaymentInfo | None,
        dtype: DiscountType, applied: list[DiscountBreakdown],
    ) -> Decimal:
        candidates = self._applicable_rules(item, payment_info, dtype)
        if not candidates:
            return price
        return self._apply_rule(price, max(candidates, key=lambda r: r.percentage), applied)

    @staticmethod
    def _apply_rule(
        price: Decimal, rule: DiscountRule, applied: list[DiscountBreakdown],
    ) -> Decimal:
        amount, new_price = rule.calculate(price)
        applied.append(DiscountBreakdown(
            discount_type=rule.discount_type, description=rule.description,
            percentage=rule.percentage, amount=amount,
            price_before=price, price_after=new_price,
        ))
        return new_price
