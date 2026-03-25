"""Dummy data modelling the assignment's example scenario."""

from discounts import BankOffer, BrandDiscount, CategoryDiscount, VoucherDiscount
from models import CartItem, PaymentInfo, Product

# ── Products ────────────────────────────────────────────────

puma_tshirt = Product(
    id="PROD-001", name="PUMA Essentials Logo Tee",
    brand="PUMA", category="T-Shirts", mrp=1499.0,
)

nike_shoes = Product(
    id="PROD-002", name="Nike Air Max 90",
    brand="Nike", category="Shoes", mrp=8995.0,
)

puma_jacket = Product(
    id="PROD-003", name="PUMA Windbreaker Jacket",
    brand="PUMA", category="Jackets", mrp=3999.0,
)

# ── Discount rules (4 separate lists) ─────────────────────

brand_discounts = [BrandDiscount(brand="PUMA", min_discount_pct=40.0)]
category_discounts = [CategoryDiscount(category="T-Shirts", discount_pct=10.0)]
vouchers = [VoucherDiscount(code="SUPER69", discount_pct=69.0)]
bank_offers = [BankOffer(bank="ICICI", discount_pct=10.0)]

# ── Sample carts ────────────────────────────────────────────

sample_cart = [
    CartItem(product=puma_tshirt, quantity=2),
    CartItem(product=nike_shoes, quantity=1),
    CartItem(product=puma_jacket, quantity=1),
]

# ── Payment profiles ───────────────────────────────────────

icici_payment = PaymentInfo(bank="ICICI", card_type="credit")
hdfc_payment = PaymentInfo(bank="HDFC", card_type="debit")
