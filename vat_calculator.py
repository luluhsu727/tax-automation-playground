"""Utilities for generating VAT payable by jurisdiction."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import argparse
import json
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _to_decimal(value: Any, field_name: str) -> Decimal:
    """Convert incoming numeric value to Decimal."""
    if value is None:
        raise ValueError(f"Missing required field: {field_name}")
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid numeric value for {field_name}: {value}") from exc


def _calculate_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    """Calculate VAT amount for one transaction."""
    explicit_vat = transaction.get("vat_amount")
    if explicit_vat is not None:
        return _to_decimal(explicit_vat, "vat_amount").quantize(TWOPLACES, ROUND_HALF_UP)

    taxable_amount = transaction.get("taxable_amount", transaction.get("amount"))
    vat_rate = transaction.get("vat_rate")

    taxable = _to_decimal(taxable_amount, "taxable_amount/amount")
    rate = _to_decimal(vat_rate, "vat_rate")
    return (taxable * rate).quantize(TWOPLACES, ROUND_HALF_UP)


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Generate net VAT payable by jurisdiction.

    Net VAT payable = output VAT from sales - input VAT from purchases.

    Expected transaction fields:
      - jurisdiction: jurisdiction code/name (required)
      - kind: "sale" or "purchase" (required)
      - Either:
          - vat_amount
        Or:
          - taxable_amount (or amount) and vat_rate
    """

    vat_by_jurisdiction: dict[str, Decimal] = {}

    for transaction in transactions:
        jurisdiction = str(transaction.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Each transaction must include a jurisdiction")

        kind = str(transaction.get("kind", "")).strip().lower()
        if kind not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction kind '{kind}'. Use 'sale' or 'purchase'."
            )

        vat_amount = _calculate_vat_amount(transaction)
        sign = Decimal("1") if kind == "sale" else Decimal("-1")
        running_total = vat_by_jurisdiction.get(jurisdiction, Decimal("0.00"))
        vat_by_jurisdiction[jurisdiction] = (running_total + sign * vat_amount).quantize(
            TWOPLACES, ROUND_HALF_UP
        )

    return vat_by_jurisdiction


def _decimal_map_to_string_map(values: Mapping[str, Decimal]) -> dict[str, str]:
    """Convert Decimal mapping to serializable fixed-precision strings."""
    return {key: f"{value:.2f}" for key, value in values.items()}


def main() -> None:
    """CLI entrypoint.

    Input must be a JSON file containing an array of transaction objects.
    """
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction data."
    )
    parser.add_argument(
        "input_file",
        help="Path to JSON file containing an array of transactions",
    )
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as infile:
        transactions = json.load(infile)

    if not isinstance(transactions, list):
        raise ValueError("Input JSON must be an array of transaction objects.")

    result = generate_vat_to_be_paid_by_jurisdiction(transactions)
    print(json.dumps(_decimal_map_to_string_map(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
