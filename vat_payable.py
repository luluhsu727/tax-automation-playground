"""Compute VAT payable for each jurisdiction from transaction data."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """A single tax-relevant transaction."""

    jurisdiction: str
    transaction_type: str  # "sale" or "purchase"
    amount: Decimal
    vat_rate: Decimal | None = None
    vat_amount: Decimal | None = None

    @staticmethod
    def from_dict(raw: dict) -> "Transaction":
        jurisdiction = str(raw["jurisdiction"]).strip()
        if not jurisdiction:
            raise ValueError("jurisdiction must be a non-empty string")

        transaction_type = str(raw["transaction_type"]).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError("transaction_type must be 'sale' or 'purchase'")

        amount = _to_decimal(raw.get("amount", "0"))
        vat_rate = raw.get("vat_rate")
        vat_amount = raw.get("vat_amount")

        parsed_vat_rate = _to_decimal(vat_rate) if vat_rate is not None else None
        parsed_vat_amount = _to_decimal(vat_amount) if vat_amount is not None else None

        if parsed_vat_amount is None and parsed_vat_rate is None:
            raise ValueError(
                "each transaction must include either vat_amount or vat_rate"
            )

        return Transaction(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            amount=amount,
            vat_rate=parsed_vat_rate,
            vat_amount=parsed_vat_amount,
        )

    def resolve_vat_amount(self) -> Decimal:
        if self.vat_amount is not None:
            return self.vat_amount
        # For rate-based rows, VAT = taxable amount * VAT rate.
        return self.amount * self.vat_rate  # type: ignore[operator]


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, dict[str, Decimal]]:
    """
    Return output VAT, input VAT, and VAT payable per jurisdiction.

    VAT payable is calculated as:
      output_vat - input_vat
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
            "vat_payable": Decimal("0"),
        }
    )

    for tx in transactions:
        vat = tx.resolve_vat_amount()
        if tx.transaction_type == "sale":
            totals[tx.jurisdiction]["output_vat"] += vat
        else:
            totals[tx.jurisdiction]["input_vat"] += vat

    for jurisdiction_totals in totals.values():
        jurisdiction_totals["vat_payable"] = (
            jurisdiction_totals["output_vat"] - jurisdiction_totals["input_vat"]
        )

        for key, value in list(jurisdiction_totals.items()):
            jurisdiction_totals[key] = value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    return dict(totals)


def load_transactions(path: str) -> list[Transaction]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("input file must contain a JSON array of transactions")

    return [Transaction.from_dict(item) for item in payload]


def format_results(
    totals: dict[str, dict[str, Decimal]],
) -> dict[str, dict[str, str]]:
    """Convert Decimal fields to fixed-precision strings for JSON output."""
    return {
        jurisdiction: {
            "output_vat": f"{data['output_vat']:.2f}",
            "input_vat": f"{data['input_vat']:.2f}",
            "vat_payable": f"{data['vat_payable']:.2f}",
        }
        for jurisdiction, data in totals.items()
    }


def _to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction."
    )
    parser.add_argument("--input", required=True, help="Path to transactions JSON file")
    parser.add_argument(
        "--output",
        help="Optional path for output JSON file; prints to stdout if omitted",
    )
    args = parser.parse_args()

    transactions = load_transactions(args.input)
    totals = calculate_vat_payable_by_jurisdiction(transactions)
    payload = {"jurisdictions": format_results(totals)}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        return

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
