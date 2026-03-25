"""Demo script — run the discount service against sample data."""

from fake_data import (
    bank_offers, brand_discounts, category_discounts, vouchers,
    icici_payment, puma_tshirt, sample_cart, CartItem,
)
from service import DiscountService


def main() -> None:
    svc = DiscountService(brand_discounts, category_discounts, vouchers, bank_offers)

    print("=" * 62)
    print("  Unifize Fashion Store — Discount Calculator Demo")
    print("=" * 62)

    _header("Scenario 1: Full cart + ICICI card (no voucher)")
    _print_results(svc.calculate_cart_discounts(sample_cart, icici_payment))

    _header("Scenario 2: PUMA Tee + SUPER69 voucher + ICICI card")
    _print_results(
        svc.calculate_cart_discounts(
            [CartItem(product=puma_tshirt)], icici_payment, voucher_code="SUPER69"
        )
    )

    _header("Scenario 3: Invalid voucher code")
    try:
        svc.calculate_cart_discounts([CartItem(product=puma_tshirt)], voucher_code="FAKECODE")
    except ValueError as exc:
        print(f"  Error: {exc}")


def _header(title: str) -> None:
    print(f"\n{'─' * 62}\n  {title}\n{'─' * 62}")


def _print_results(results: list) -> None:
    for r in results:
        print(f"\n  {r.product_name} (qty {r.quantity})")
        print(f"    MRP:         ₹{r.original_price}")
        for d in r.applied_discounts:
            print(f"    ↳ {d.description}")
            print(f"        −{d.percentage}%  (₹{d.amount})  →  ₹{d.price_after}")
        print(f"    Final price: ₹{r.final_price}  ({r.total_discount_percentage}% off)")
        print(f"    You save:    ₹{r.total_discount} per unit")


if __name__ == "__main__":
    main()
