"""Core discount service — orchestrates discount stacking and calculation."""

from __future__ import annotations

from discounts import BankOffer, BrandDiscount, CategoryDiscount, VoucherDiscount
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

    def __init__(
        self,
        brand_discounts: list[BrandDiscount],
        category_discounts: list[CategoryDiscount],
        vouchers: list[VoucherDiscount],
        bank_offers: list[BankOffer],
    ) -> None:
        self.brand_discounts = brand_discounts
        self.category_discounts = category_discounts
        self.vouchers = vouchers
        self.bank_offers = bank_offers

    # ── Public API ──────────────────────────────────────────

    def validate_discount_code(self, code: str) -> VoucherDiscount | None:
        """Return the matching VoucherDiscount or None if the code is invalid."""
        if not code or not code.strip():
            return None
        normalised = code.strip().upper()
        for v in self.vouchers:
            if v.code.upper() == normalised:
                return v
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
            price = item.product.mrp  # float — imprecise for compound discounts

            # Phase 1: Brand
            brand_matches = [d for d in self.brand_discounts if d.is_applicable(item.product)]
            if brand_matches:
                best = max(brand_matches, key=lambda d: d.min_discount_pct)
                amount = round(price * best.min_discount_pct / 100, 2)
                new_price = round(price - amount, 2)
                applied.append(DiscountBreakdown(
                    discount_type=DiscountType.BRAND, description=best.description,
                    percentage=best.min_discount_pct, amount=amount,
                    price_before=price, price_after=new_price,
                ))
                price = new_price

            # Phase 2: Category
            cat_matches = [d for d in self.category_discounts if d.is_applicable(item.product)]
            if cat_matches:
                best = max(cat_matches, key=lambda d: d.discount_pct)
                amount = round(price * best.discount_pct / 100, 2)
                new_price = round(price - amount, 2)
                applied.append(DiscountBreakdown(
                    discount_type=DiscountType.CATEGORY, description=best.description,
                    percentage=best.discount_pct, amount=amount,
                    price_before=price, price_after=new_price,
                ))
                price = new_price

            # Phase 3: Voucher
            if voucher:
                amount = round(price * voucher.discount_pct / 100, 2)
                new_price = round(price - amount, 2)
                applied.append(DiscountBreakdown(
                    discount_type=DiscountType.VOUCHER, description=voucher.description,
                    percentage=voucher.discount_pct, amount=amount,
                    price_before=price, price_after=new_price,
                ))
                price = new_price

            # Phase 4: Bank offer
            bank_matches = [o for o in self.bank_offers if o.is_applicable(item.product, payment_info)]
            if bank_matches:
                best = max(bank_matches, key=lambda o: o.discount_pct)
                amount = round(price * best.discount_pct / 100, 2)
                new_price = round(price - amount, 2)
                applied.append(DiscountBreakdown(
                    discount_type=DiscountType.BANK, description=best.description,
                    percentage=best.discount_pct, amount=amount,
                    price_before=price, price_after=new_price,
                ))
                price = new_price

            total_discount = round(item.product.mrp - price, 2)
            total_pct = round(total_discount / item.product.mrp * 100, 2) if item.product.mrp > 0 else 0.0

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
