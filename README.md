# Unifize — Fashion E-Commerce Discount Service

A discount calculation service for a fashion e-commerce platform supporting four discount types.

## Quick Start

```bash
# Create a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the demo
python main.py

# Run tests
pytest -v
```

## Discount Types

| Type | Example | Scope |
|------|---------|-------|
| Brand | "Min 40% off on PUMA" | All products of a brand |
| Category | "Extra 10% off on T-Shirts" | All products in a category |
| Voucher | `SUPER69` → 69% off | Any product |
| Bank Offer | "10% instant discount on ICICI" | Payment-method gated |

## Stacking Order

Discounts are applied sequentially in this order:

```
MRP
 │
 ├─ 1. Brand discount        (on MRP)
 ├─ 2. Category discount      (on brand-discounted price)
 ├─ 3. Voucher code           (on further-reduced price)
 └─ 4. Bank offer             (applied last)
 │
 ▼
Final Price
```

**Example — PUMA T-Shirt (MRP ₹1 499) with ICICI card:**

| Step | Discount | Amount | Running Price |
|------|----------|--------|--------------|
| Brand 40% | ₹599.60 | ₹899.40 |
| Category 10% | ₹89.94 | ₹809.46 |
| Bank 10% | ₹80.95 | **₹728.51** |

## Architecture

```
models.py       ← Data classes (Product, CartItem, PaymentInfo, DiscountedPrice)
discounts.py    ← Discount type classes (BrandDiscount, CategoryDiscount, Voucher, BankOffer)
service.py      ← DiscountService (stacking logic)
fake_data.py    ← Sample products and discount rules
main.py         ← CLI demo
tests/          ← pytest suite
```

## Assumptions

1. **Best-in-tier wins** — If multiple brand discounts apply to the same product, only the highest-percentage one is used.
2. **Per-unit pricing** — Discounts are calculated on the unit MRP; quantity only affects the line total.
3. **Sequential compounding** — Each tier's percentage applies to the already discounted price, not the original MRP.
4. **Voucher is universal** — A valid voucher code applies to every item in the cart.
5. **Bank offers require payment info** — If no payment information is supplied, bank offers are skipped.
