"""Tests for the discount service."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from discounts import BankOffer, BrandDiscount, CategoryDiscount, VoucherDiscount
from models import CartItem, DiscountType, PaymentInfo, Product
from service import DiscountService


# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture
def puma_tshirt() -> Product:
    return Product(id="P1", name="PUMA Tee", brand="PUMA", category="T-Shirts", mrp=1499.0)


@pytest.fixture
def nike_shoes() -> Product:
    return Product(id="P2", name="Nike Air Max", brand="Nike", category="Shoes", mrp=8995.0)


@pytest.fixture
def all_rules():
    return (
        [BrandDiscount(brand="PUMA", min_discount_pct=40.0)],
        [CategoryDiscount(category="T-Shirts", discount_pct=10.0)],
        [VoucherDiscount(code="SUPER69", discount_pct=69.0)],
        [BankOffer(bank="ICICI", discount_pct=10.0)],
    )


@pytest.fixture
def svc(all_rules) -> DiscountService:
    return DiscountService(*all_rules)


@pytest.fixture
def icici() -> PaymentInfo:
    return PaymentInfo(bank="ICICI", card_type="credit")


@pytest.fixture
def hdfc() -> PaymentInfo:
    return PaymentInfo(bank="HDFC", card_type="debit")


# ── Stacking order: brand → category → bank ────────────────


class TestStackingOrder:
    """PUMA T-shirt with ICICI card (no voucher).

    MRP  = 1499.00
    Brand 40%  → 599.60 → 899.40
    Cat   10%  →  89.94 → 809.46
    Bank  10%  →  80.95 → 728.51
    """

    def test_final_price(self, svc, puma_tshirt, icici):
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)], icici)
        assert result.final_price == 728.51

    def test_three_discounts_applied(self, svc, puma_tshirt, icici):
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)], icici)
        assert len(result.applied_discounts) == 3

    def test_discount_types_in_order(self, svc, puma_tshirt, icici):
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)], icici)
        types = [d.discount_type for d in result.applied_discounts]
        assert types == [DiscountType.BRAND, DiscountType.CATEGORY, DiscountType.BANK]

    def test_each_step_applies_to_reduced_price(self, svc, puma_tshirt, icici):
        """Category discount must apply to the brand-discounted price, not MRP."""
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)], icici)
        _, cat, _ = result.applied_discounts
        assert cat.price_before == 899.40


# ── Full stacking with voucher ──────────────────────────────


class TestStackingWithVoucher:
    def test_final_price(self, svc, puma_tshirt, icici):
        [result] = svc.calculate_cart_discounts(
            [CartItem(puma_tshirt)], icici, voucher_code="SUPER69"
        )
        assert result.final_price == 225.84

    def test_four_discounts_applied_in_order(self, svc, puma_tshirt, icici):
        [result] = svc.calculate_cart_discounts(
            [CartItem(puma_tshirt)], icici, voucher_code="SUPER69"
        )
        types = [d.discount_type for d in result.applied_discounts]
        assert types == [
            DiscountType.BRAND, DiscountType.CATEGORY,
            DiscountType.VOUCHER, DiscountType.BANK,
        ]


# ── Discount applicability ──────────────────────────────────


class TestApplicability:
    def test_nike_gets_no_brand_discount(self, svc, nike_shoes, icici):
        [result] = svc.calculate_cart_discounts([CartItem(nike_shoes)], icici)
        types = [d.discount_type for d in result.applied_discounts]
        assert DiscountType.BRAND not in types

    def test_nike_gets_bank_offer_only(self, svc, nike_shoes, icici):
        [result] = svc.calculate_cart_discounts([CartItem(nike_shoes)], icici)
        assert len(result.applied_discounts) == 1
        assert result.final_price == 8095.50

    def test_bank_offer_skipped_for_non_matching_bank(self, svc, puma_tshirt, hdfc):
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)], hdfc)
        types = [d.discount_type for d in result.applied_discounts]
        assert DiscountType.BANK not in types

    def test_bank_offer_skipped_when_no_payment_info(self, svc, puma_tshirt):
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)])
        types = [d.discount_type for d in result.applied_discounts]
        assert DiscountType.BANK not in types


# ── Voucher validation ──────────────────────────────────────


class TestVoucherValidation:
    def test_valid_code_returns_voucher_object(self, svc):
        voucher = svc.validate_discount_code("SUPER69")
        assert voucher is not None
        assert voucher.discount_pct == 69.0

    def test_case_insensitive_lookup(self, svc):
        assert svc.validate_discount_code("super69") is not None

    def test_invalid_code_returns_none(self, svc):
        assert svc.validate_discount_code("BOGUS") is None

    def test_empty_code_returns_none(self, svc):
        assert svc.validate_discount_code("") is None

    def test_invalid_code_raises_on_cart_calculation(self, svc, puma_tshirt):
        with pytest.raises(ValueError, match="Invalid voucher code 'NOPE'"):
            svc.calculate_cart_discounts([CartItem(puma_tshirt)], voucher_code="NOPE")


# ── Edge cases ──────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_cart_returns_empty_list(self, svc, icici):
        assert svc.calculate_cart_discounts([], icici) == []

    def test_no_rules_means_no_discount(self, puma_tshirt):
        svc = DiscountService([], [], [], [])
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt)])
        assert result.final_price == 1499.0
        assert result.applied_discounts == []

    def test_quantity_stored_but_prices_are_per_unit(self, svc, puma_tshirt, icici):
        [result] = svc.calculate_cart_discounts([CartItem(puma_tshirt, quantity=3)], icici)
        assert result.quantity == 3
        assert result.original_price == 1499.0

    def test_multiple_items_discounted_independently(self, svc, puma_tshirt, nike_shoes, icici):
        results = svc.calculate_cart_discounts(
            [CartItem(puma_tshirt), CartItem(nike_shoes)], icici
        )
        assert len(results) == 2
        assert len(results[0].applied_discounts) == 3
        assert len(results[1].applied_discounts) == 1


# ── Model validation ────────────────────────────────────────


class TestModelValidation:
    def test_negative_mrp_raises(self):
        with pytest.raises(ValueError, match="MRP must be positive"):
            Product(id="X", name="X", brand="X", category="X", mrp=-1.0)

    def test_zero_quantity_raises(self, puma_tshirt):
        with pytest.raises(ValueError, match="Quantity must be at least 1"):
            CartItem(product=puma_tshirt, quantity=0)
