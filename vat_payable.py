"""Calculate VAT payable by jurisdiction.

Usage:
    python vat_payable.py transactions.json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

MONEY_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction.

    transaction_type:
      - "sale": VAT collected (increases payable VAT)
      - "purchase": VAT paid (decreases payable VAT)
    """

    jurisdiction: str
    transaction_type: str
    vat_amount: Decimal


def _to_decimal(raw: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {raw!r}") from exc


def _to_money(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def transaction_from_record(record: dict[str, object]) -> Transaction:
    """Create a Transaction from a dictionary record.

    Supported record shapes:
      1) {"jurisdiction": "...", "transaction_type": "sale|purchase", "vat_amount": 12.34}
      2) {
            "jurisdiction": "...",
            "transaction_type": "sale|purchase",
            "net_amount": 100.00,
            "vat_rate": 0.2 or 20
         }
    """

    jurisdiction = str(record.get("jurisdiction", "")).strip()
    if not jurisdiction:
        raise ValueError("Record is missing a non-empty 'jurisdiction'")

    tx_type_raw = record.get("transaction_type", record.get("type"))
    tx_type = str(tx_type_raw).strip().lower()
    if tx_type not in {"sale", "purchase"}:
        raise ValueError(
            "Record must contain transaction_type/type as 'sale' or 'purchase'"
        )

    if "vat_amount" in record:
        vat_amount = _to_decimal(record["vat_amount"], "vat_amount")
    else:
        if "net_amount" not in record or "vat_rate" not in record:
            raise ValueError(
                "Record must contain either 'vat_amount' or both "
                "'net_amount' and 'vat_rate'"
            )
        net_amount = _to_decimal(record["net_amount"], "net_amount")
        vat_rate = _to_decimal(record["vat_rate"], "vat_rate")
        # Accept either decimal rates (0.2) or percentages (20)
        if vat_rate > 1:
            vat_rate = vat_rate / Decimal("100")
        vat_amount = net_amount * vat_rate

    if vat_amount < 0:
        raise ValueError("VAT amount cannot be negative")

    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=tx_type,
        vat_amount=_to_money(vat_amount),
    )


def load_transactions(path: str | Path) -> list[Transaction]:
    file_path = Path(path)
    records = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Input JSON must be an array of transaction records")
    return [transaction_from_record(record) for record in records]


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Return net VAT payable per jurisdiction.

    Net VAT payable = VAT from sales - VAT from purchases.
    """

    totals: dict[str, Decimal] = {}
    for transaction in transactions:
        current_total = totals.get(transaction.jurisdiction, Decimal("0"))
        if transaction.transaction_type == "sale":
            current_total += transaction.vat_amount
        elif transaction.transaction_type == "purchase":
            current_total -= transaction.vat_amount
        else:
            raise ValueError(f"Unknown transaction type: {transaction.transaction_type}")
        totals[transaction.jurisdiction] = current_total

    normalized: dict[str, Decimal] = {}
    for jurisdiction, total in totals.items():
        if floor_at_zero and total < 0:
            total = Decimal("0")
        normalized[jurisdiction] = _to_money(total)
    return normalized


def _format_report(vat_by_jurisdiction: dict[str, Decimal]) -> str:
    if not vat_by_jurisdiction:
        return "No transactions."
    lines = []
    for jurisdiction in sorted(vat_by_jurisdiction):
        lines.append(f"{jurisdiction}: {vat_by_jurisdiction[jurisdiction]:.2f}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction."
    )
    parser.add_argument("input_file", help="Path to input JSON transaction file")
    parser.add_argument(
        "--floor-at-zero",
        action="store_true",
        help="Set negative net VAT values to 0.00",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON object instead of plain text",
    )
    args = parser.parse_args()

    transactions = load_transactions(args.input_file)
    vat_by_jurisdiction = calculate_vat_payable_by_jurisdiction(
        transactions, floor_at_zero=args.floor_at_zero
    )

    if args.json:
        # Convert Decimals to strings to preserve exact 2dp values.
        payload = {k: f"{v:.2f}" for k, v in sorted(vat_by_jurisdiction.items())}
        print(json.dumps(payload, indent=2))
    else:
        print(_format_report(vat_by_jurisdiction))


if __name__ == "__main__":
    main()
