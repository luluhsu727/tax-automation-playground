from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class TaxTransaction:
    """Represents one taxable transaction."""

    jurisdiction: str
    kind: str
    vat_amount: Decimal


def _to_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        raise ValueError("Value cannot be None.")
    return Decimal(str(value))


def _normalize_kind(kind: str) -> str:
    normalized = kind.strip().lower()
    if normalized in {"sale", "sales", "output"}:
        return "sale"
    if normalized in {"purchase", "purchases", "input"}:
        return "purchase"
    raise ValueError(
        "Transaction kind must be one of sale/sales/output or purchase/purchases/input."
    )


def build_transaction(record: dict) -> TaxTransaction:
    """
    Build a TaxTransaction from a dictionary.

    Required keys:
      - jurisdiction: str
      - kind: sale|purchase (aliases accepted)

    VAT amount can be provided either as:
      - vat_amount, or
      - net_amount + vat_rate
    """

    try:
        jurisdiction = str(record["jurisdiction"]).strip()
        kind = _normalize_kind(str(record["kind"]))
    except KeyError as exc:
        raise ValueError(f"Missing required key: {exc.args[0]}") from exc

    if not jurisdiction:
        raise ValueError("Jurisdiction cannot be empty.")

    if "vat_amount" in record and record["vat_amount"] is not None:
        vat_amount = _to_decimal(record["vat_amount"])
    else:
        if "net_amount" not in record or "vat_rate" not in record:
            raise ValueError(
                "Record must include vat_amount or both net_amount and vat_rate."
            )
        vat_amount = _to_decimal(record["net_amount"]) * _to_decimal(record["vat_rate"])

    if vat_amount < 0:
        raise ValueError("VAT amount must be non-negative.")

    return TaxTransaction(
        jurisdiction=jurisdiction,
        kind=kind,
        vat_amount=vat_amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
    )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[TaxTransaction | dict],
) -> dict[str, Decimal]:
    """
    Compute VAT payable by jurisdiction.

    VAT payable = output VAT (sales) - input VAT (purchases).
    Result can be negative (VAT credit).
    """

    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for transaction in transactions:
        item = (
            transaction
            if isinstance(transaction, TaxTransaction)
            else build_transaction(transaction)
        )

        if item.kind == "sale":
            totals[item.jurisdiction] += item.vat_amount
        else:
            totals[item.jurisdiction] -= item.vat_amount

    # Freeze as normal dict and normalize rounding
    return {
        jurisdiction: amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        for jurisdiction, amount in totals.items()
    }


def _load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)
    if not isinstance(data, list):
        raise ValueError("Input JSON must be an array of transaction records.")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable per jurisdiction from JSON transactions."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to JSON file containing an array of transaction records.",
    )
    args = parser.parse_args()

    records = _load_json(args.input_file)
    totals = calculate_vat_payable_by_jurisdiction(records)
    serializable = {k: str(v) for k, v in sorted(totals.items())}
    print(json.dumps(serializable, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
