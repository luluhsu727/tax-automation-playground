"""VAT payable aggregation by jurisdiction.

The main entry point is ``calculate_vat_payable_by_jurisdiction`` which
returns net VAT payable per jurisdiction:

    VAT payable = output VAT on sales - input VAT on purchases
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, TextIO

TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """Single taxable transaction.

    Attributes:
        jurisdiction: Tax jurisdiction identifier (e.g. "DE", "UK", "CA-ON").
        net_amount: Amount excluding VAT.
        vat_rate: VAT rate as a decimal fraction (e.g. 0.2 for 20%).
        transaction_type: Either "sale" (output VAT) or "purchase" (input VAT).
    """

    jurisdiction: str
    net_amount: Decimal
    vat_rate: Decimal
    transaction_type: str

    @classmethod
    def from_mapping(cls, record: Mapping[str, object]) -> "Transaction":
        """Create ``Transaction`` from a dictionary-like record."""
        return cls(
            jurisdiction=str(record["jurisdiction"]),
            net_amount=_to_decimal(record["net_amount"]),
            vat_rate=_to_decimal(record["vat_rate"]),
            transaction_type=str(record["transaction_type"]),
        )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, Decimal]:
    """Aggregate VAT payable per jurisdiction.

    Args:
        transactions: Iterable of ``Transaction`` objects or dict-like records.

    Returns:
        Dict keyed by jurisdiction where each value is net VAT payable as Decimal.
    """

    totals: dict[str, Decimal] = {}
    for row in transactions:
        tx = row if isinstance(row, Transaction) else Transaction.from_mapping(row)
        if tx.vat_rate < 0:
            raise ValueError(f"vat_rate must be non-negative, got {tx.vat_rate}.")
        if tx.net_amount < 0:
            raise ValueError(f"net_amount must be non-negative, got {tx.net_amount}.")

        tx_type = tx.transaction_type.strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type={tx.transaction_type!r}; "
                "expected 'sale' or 'purchase'."
            )

        vat_value = (tx.net_amount * tx.vat_rate).quantize(TWOPLACES, ROUND_HALF_UP)
        signed_vat = vat_value if tx_type == "sale" else -vat_value
        totals[tx.jurisdiction] = totals.get(tx.jurisdiction, Decimal("0")) + signed_vat

    # Quantize final totals for stable output and deterministic downstream formatting.
    return {
        jurisdiction: amount.quantize(TWOPLACES, ROUND_HALF_UP)
        for jurisdiction, amount in totals.items()
    }


def calculate_vat_payable_as_strings(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, str]:
    """Same aggregation as string output for serialization-friendly responses."""
    return {
        jurisdiction: format(amount, ".2f")
        for jurisdiction, amount in calculate_vat_payable_by_jurisdiction(
            transactions
        ).items()
    }


def generate_vat_payable_report(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, str]:
    """Public helper used by automations and APIs."""
    return calculate_vat_payable_as_strings(transactions)


def _load_json_transactions(input_file: TextIO) -> list[Mapping[str, object]]:
    payload = json.load(input_file)
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transaction records.")
    for idx, record in enumerate(payload):
        if not isinstance(record, dict):
            raise ValueError(f"Record at index {idx} must be an object.")
    return payload


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for VAT-payable generation by jurisdiction."""
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction JSON."
    )
    parser.add_argument(
        "--input",
        default="-",
        help="Path to JSON file with transactions. Use '-' for stdin.",
    )
    args = parser.parse_args(argv)

    try:
        if args.input == "-":
            records = _load_json_transactions(sys.stdin)
        else:
            with open(args.input, "r", encoding="utf-8") as fp:
                records = _load_json_transactions(fp)
        result = generate_vat_payable_report(records)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(dict(sorted(result.items())), separators=(",", ":")))
    return 0


def _to_decimal(value: object) -> Decimal:
    """Convert user input to Decimal via string for numeric stability."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


if __name__ == "__main__":
    raise SystemExit(main())
