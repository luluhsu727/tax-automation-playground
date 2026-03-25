"""VAT payable calculation per jurisdiction.

This module aggregates transaction-level VAT into jurisdiction-level totals:
- output_vat: VAT collected on sales
- input_vat: VAT paid on purchases
- vat_payable: output_vat - input_vat
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping


TWOPLACES = Decimal("0.01")


@dataclass
class VATSummary:
    output_vat: Decimal = Decimal("0.00")
    input_vat: Decimal = Decimal("0.00")

    @property
    def vat_payable(self) -> Decimal:
        return self.output_vat - self.input_vat


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Invalid numeric value for '{field_name}': {value}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Support both decimal rates (0.2) and percentage rates (20)."""
    if rate < 0:
        raise ValueError("VAT rate cannot be negative")
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    """Return VAT amount for a single transaction."""
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
        return _quantize_money(vat_amount)

    if "taxable_amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            "Each transaction must include either 'vat_amount' or both "
            "'taxable_amount' and 'vat_rate'"
        )

    taxable_amount = _to_decimal(transaction["taxable_amount"], "taxable_amount")
    vat_rate = _normalize_rate(_to_decimal(transaction["vat_rate"], "vat_rate"))
    return _quantize_money(taxable_amount * vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, VATSummary]:
    """Aggregate VAT totals by jurisdiction.

    Required fields for each transaction:
    - jurisdiction: str
    - transaction_type: "sale" or "purchase"
    - vat_amount OR (taxable_amount and vat_rate)
    """
    totals: defaultdict[str, VATSummary] = defaultdict(VATSummary)

    for idx, transaction in enumerate(transactions, start=1):
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction or not str(jurisdiction).strip():
            raise ValueError(f"Transaction #{idx} is missing 'jurisdiction'")
        jurisdiction = str(jurisdiction).strip()

        transaction_type = transaction.get("transaction_type")
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction #{idx} has invalid 'transaction_type': {transaction_type}. "
                "Expected 'sale' or 'purchase'."
            )

        vat_amount = calculate_transaction_vat(transaction)

        bucket = totals[jurisdiction]
        if transaction_type == "sale":
            bucket.output_vat = _quantize_money(bucket.output_vat + vat_amount)
        else:
            bucket.input_vat = _quantize_money(bucket.input_vat + vat_amount)

    return dict(sorted(totals.items(), key=lambda item: item[0]))


def _to_json_serializable(result: Mapping[str, VATSummary]) -> dict[str, dict[str, str]]:
    serializable: dict[str, dict[str, str]] = {}
    for jurisdiction, summary in result.items():
        serializable[jurisdiction] = {
            "output_vat": format(summary.output_vat, ".2f"),
            "input_vat": format(summary.input_vat, ".2f"),
            "vat_payable": format(summary.vat_payable, ".2f"),
        }
    return serializable


def _format_table(result: Mapping[str, VATSummary]) -> str:
    header = f"{'Jurisdiction':<16} {'Output VAT':>12} {'Input VAT':>12} {'VAT Payable':>12}"
    rows = [header, "-" * len(header)]
    for jurisdiction, summary in result.items():
        rows.append(
            f"{jurisdiction:<16} "
            f"{format(summary.output_vat, '.2f'):>12} "
            f"{format(summary.input_vat, '.2f'):>12} "
            f"{format(summary.vat_payable, '.2f'):>12}"
        )
    return "\n".join(rows)


def _load_transactions(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be an array of transactions")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable per jurisdiction from transaction JSON."
    )
    parser.add_argument("input_file", type=Path, help="Path to JSON transactions file")
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format (default: table)",
    )
    args = parser.parse_args()

    transactions = _load_transactions(args.input_file)
    result = generate_vat_payable_by_jurisdiction(transactions)

    if args.format == "json":
        print(json.dumps(_to_json_serializable(result), indent=2))
    else:
        print(_format_table(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
