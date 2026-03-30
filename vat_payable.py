"""Generate VAT payable per jurisdiction.

The module can be imported as a library or executed as a CLI:

    python vat_payable.py /path/to/transactions.json

Input JSON format:
[
  {
    "jurisdiction": "DE",
    "transaction_type": "sale",  # "sale" or "purchase"
    "net_amount": "100.00",
    "vat_rate": "0.19"
  }
]
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Literal

CENTS = Decimal("0.01")


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    """Parse numeric values safely into Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction for a single jurisdiction."""

    jurisdiction: str
    transaction_type: Literal["sale", "purchase"]
    net_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal | None = None

    def resolved_vat_amount(self) -> Decimal:
        """Return explicit VAT or derive VAT from net amount and VAT rate."""
        if self.vat_amount is not None:
            return _round_money(self.vat_amount)
        return _round_money(self.net_amount * self.vat_rate)

    @classmethod
    def from_dict(cls, payload: dict) -> "Transaction":
        transaction_type = payload["transaction_type"].strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type '{transaction_type}'. "
                "Expected 'sale' or 'purchase'."
            )

        jurisdiction = payload["jurisdiction"].strip()
        if not jurisdiction:
            raise ValueError("jurisdiction cannot be blank")

        vat_amount_raw = payload.get("vat_amount")
        vat_amount = _to_decimal(vat_amount_raw) if vat_amount_raw is not None else None

        return cls(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,  # type: ignore[arg-type]
            net_amount=_to_decimal(payload["net_amount"]),
            vat_rate=_to_decimal(payload["vat_rate"]),
            vat_amount=vat_amount,
        )


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, dict[str, Decimal]]:
    """Aggregate output VAT, input VAT, and payable VAT per jurisdiction."""
    totals: dict[str, dict[str, Decimal]] = {}

    for transaction in transactions:
        jurisdiction_totals = totals.setdefault(
            transaction.jurisdiction,
            {
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
                "vat_payable": Decimal("0.00"),
            },
        )
        vat = transaction.resolved_vat_amount()
        if transaction.transaction_type == "sale":
            jurisdiction_totals["output_vat"] += vat
        else:
            jurisdiction_totals["input_vat"] += vat

    for jurisdiction_totals in totals.values():
        jurisdiction_totals["output_vat"] = _round_money(jurisdiction_totals["output_vat"])
        jurisdiction_totals["input_vat"] = _round_money(jurisdiction_totals["input_vat"])
        jurisdiction_totals["vat_payable"] = _round_money(
            jurisdiction_totals["output_vat"] - jurisdiction_totals["input_vat"]
        )

    return totals


def _serialize_for_json(
    report: dict[str, dict[str, Decimal]],
) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {key: format(value, ".2f") for key, value in values.items()}
        for jurisdiction, values in report.items()
    }


def _read_transactions(file_path: Path) -> list[Transaction]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transactions.")
    return [Transaction.from_dict(item) for item in payload]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python vat_payable.py /path/to/transactions.json", file=sys.stderr)
        return 1

    input_path = Path(argv[1])
    transactions = _read_transactions(input_path)
    report = generate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(_serialize_for_json(report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
