"""Dummy data modelling the assignment's example scenario."""

from decimal import Decimal

from discounts import BankOffer, BrandDiscount, CategoryDiscount, VoucherDiscount
from models import CardType, CartItem, PaymentInfo, Product

# ── Products ────────────────────────────────────────────────

puma_tshirt = Product(
    id="PROD-001", name="PUMA Essentials Logo Tee",
    brand="PUMA", category="T-Shirts", mrp=Decimal("1499.00"),
)

nike_shoes = Product(
    id="PROD-002", name="Nike Air Max 90",
    brand="Nike", category="Shoes", mrp=Decimal("8995.00"),
)

puma_jacket = Product(
    id="PROD-003", name="PUMA Windbreaker Jacket",
    brand="PUMA", category="Jackets", mrp=Decimal("3999.00"),
)

# ── Active discount rules (single flat list) ───────────────

active_discounts = [
    BrandDiscount(brand="PUMA", min_discount_pct=Decimal("40")),
    CategoryDiscount(category="T-Shirts", discount_pct=Decimal("10")),
    VoucherDiscount(code="SUPER69", discount_pct=Decimal("69")),
    BankOffer(bank="ICICI", discount_pct=Decimal("10")),
]

# ── Sample carts ────────────────────────────────────────────

sample_cart = [
    CartItem(product=puma_tshirt, quantity=2),
    CartItem(product=nike_shoes, quantity=1),
    CartItem(product=puma_jacket, quantity=1),
]

# ── Payment profiles ───────────────────────────────────────

icici_payment = PaymentInfo(bank="ICICI", card_type=CardType.CREDIT)
hdfc_payment = PaymentInfo(bank="HDFC", card_type=CardType.DEBIT)
