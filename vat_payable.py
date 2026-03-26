"""Generate VAT to be paid for each jurisdiction."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping

MONEY_PLACES = Decimal("0.01")
ZERO = Decimal("0.00")
SALE_TYPES = {"sale", "sales", "output"}
PURCHASE_TYPES = {"purchase", "purchases", "input"}


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction."""

    jurisdiction: str
    transaction_type: str
    vat_amount: Decimal


def _to_decimal(raw: object, field_name: str) -> Decimal:
    if raw is None:
        raise ValueError(f"Missing required numeric field: {field_name}")
    try:
        return Decimal(str(raw).strip())
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {raw!r}") from exc


def _parse_vat_rate(raw: object) -> Decimal:
    if isinstance(raw, str) and raw.strip().endswith("%"):
        return _to_decimal(raw.strip()[:-1], "vat_rate") / Decimal("100")

    rate = _to_decimal(raw, "vat_rate")
    # Accept either decimal rates (0.2) or percentages (20).
    if rate > Decimal("1"):
        rate = rate / Decimal("100")
    return rate


def _to_money(amount: Decimal) -> Decimal:
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _normalize_transaction_type(raw_type: object) -> str:
    tx_type = str(raw_type).strip().lower()
    if tx_type in SALE_TYPES:
        return "sale"
    if tx_type in PURCHASE_TYPES:
        return "purchase"
    raise ValueError(
        "transaction_type/kind/type must be one of "
        "'sale', 'sales', 'output', 'purchase', 'purchases', or 'input'"
    )


def transaction_from_record(record: Mapping[str, object]) -> Transaction:
    """Create a Transaction from a dictionary-like record.

    Supported shapes:
      1) {"jurisdiction": "...", "transaction_type": "sale|purchase", "vat_amount": 12.34}
      2) {"jurisdiction": "...", "transaction_type": "sale|purchase", "net_amount": 100, "vat_rate": 20}
      3) transaction type aliases in `kind` or `type`
    """

    jurisdiction = str(record.get("jurisdiction", "")).strip()
    if not jurisdiction:
        raise ValueError("Record is missing a non-empty 'jurisdiction'")

    tx_type_raw = record.get("transaction_type", record.get("kind", record.get("type")))
    tx_type = _normalize_transaction_type(tx_type_raw)

    vat_amount_raw = record.get("vat_amount")
    if vat_amount_raw not in (None, ""):
        vat_amount = _to_decimal(vat_amount_raw, "vat_amount")
    else:
        if "net_amount" not in record or "vat_rate" not in record:
            raise ValueError(
                "Record must contain either 'vat_amount' or both "
                "'net_amount' and 'vat_rate'"
            )
        net_amount = _to_decimal(record["net_amount"], "net_amount")
        vat_rate = _parse_vat_rate(record["vat_rate"])
        vat_amount = net_amount * vat_rate

    if vat_amount < 0:
        raise ValueError("VAT amount cannot be negative")

    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=tx_type,
        vat_amount=_to_money(vat_amount),
    )


def load_transactions(path: str | Path) -> list[Transaction]:
    """Load transactions from JSON or CSV by file extension."""
    source = Path(path)
    extension = source.suffix.lower()

    if extension == ".json":
        records = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            raise ValueError("Input JSON must be an array of transaction records")
        return [transaction_from_record(record) for record in records]

    if extension == ".csv":
        with source.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            return [transaction_from_record(row) for row in reader]

    raise ValueError("Unsupported input file type. Use .json or .csv")


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Return net VAT payable per jurisdiction.

    Net VAT payable = VAT from sales - VAT from purchases.
    """

    totals: dict[str, Decimal] = {}
    for entry in transactions:
        transaction = (
            entry if isinstance(entry, Transaction) else transaction_from_record(entry)
        )
        current = totals.get(transaction.jurisdiction, ZERO)
        if transaction.transaction_type == "sale":
            current += transaction.vat_amount
        elif transaction.transaction_type == "purchase":
            current -= transaction.vat_amount
        totals[transaction.jurisdiction] = current

    normalized: dict[str, Decimal] = {}
    for jurisdiction, total in totals.items():
        if floor_at_zero and total < ZERO:
            total = ZERO
        normalized[jurisdiction] = _to_money(total)
    return normalized


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, dict[str, Decimal]]:
    """Return VAT output/input/net/payable breakdown per jurisdiction."""

    buckets: dict[str, dict[str, Decimal]] = {}

    for entry in transactions:
        transaction = (
            entry if isinstance(entry, Transaction) else transaction_from_record(entry)
        )
        jurisdiction_totals = buckets.setdefault(
            transaction.jurisdiction,
            {"output_vat": ZERO, "input_vat": ZERO},
        )
        if transaction.transaction_type == "sale":
            jurisdiction_totals["output_vat"] += transaction.vat_amount
        else:
            jurisdiction_totals["input_vat"] += transaction.vat_amount

    results: dict[str, dict[str, Decimal]] = {}
    for jurisdiction, totals in sorted(buckets.items()):
        output_vat = _to_money(totals["output_vat"])
        input_vat = _to_money(totals["input_vat"])
        net_vat = _to_money(output_vat - input_vat)

        if floor_at_zero and net_vat < ZERO:
            net_vat = ZERO
            vat_to_be_paid = ZERO
            vat_credit = ZERO
        else:
            vat_to_be_paid = net_vat if net_vat > ZERO else ZERO
            vat_credit = -net_vat if net_vat < ZERO else ZERO

        results[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_to_be_paid": _to_money(vat_to_be_paid),
            "vat_credit": _to_money(vat_credit),
        }

    return results


def _format_report(vat_by_jurisdiction: Mapping[str, Decimal]) -> str:
    if not vat_by_jurisdiction:
        return "No transactions."
    lines: list[str] = []
    for jurisdiction in sorted(vat_by_jurisdiction):
        lines.append(f"{jurisdiction}: {vat_by_jurisdiction[jurisdiction]:.2f}")
    return "\n".join(lines)


def _format_payable_report(
    vat_summary: Mapping[str, Mapping[str, Decimal]],
) -> str:
    if not vat_summary:
        return "No transactions."
    lines: list[str] = []
    for jurisdiction in sorted(vat_summary):
        lines.append(f"{jurisdiction}: {vat_summary[jurisdiction]['vat_to_be_paid']:.2f}")
    return "\n".join(lines)


def _serialize_summary(
    vat_summary: Mapping[str, Mapping[str, Decimal]],
) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {key: f"{value:.2f}" for key, value in values.items()}
        for jurisdiction, values in vat_summary.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument("input_file", help="Path to input JSON or CSV transaction file")
    parser.add_argument(
        "--floor-at-zero",
        action="store_true",
        help="Set negative net VAT values to 0.00",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full VAT breakdown as JSON",
    )
    args = parser.parse_args()

    transactions = load_transactions(args.input_file)
    summary = generate_vat_payable_by_jurisdiction(
        transactions, floor_at_zero=args.floor_at_zero
    )

    if args.json:
        print(json.dumps(_serialize_summary(summary), indent=2))
    else:
        print(_format_payable_report(summary))


if __name__ == "__main__":
    main()

