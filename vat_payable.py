from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return Decimal("0")
    return Decimal(str(value))


def _compute_vat_amount(record: Mapping[str, object]) -> Decimal:
    if "vat_amount" in record and str(record.get("vat_amount", "")).strip() != "":
        return _to_decimal(record["vat_amount"]).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    amount = _to_decimal(record.get("amount"))
    vat_rate = _to_decimal(record.get("vat_rate"))
    return (amount * vat_rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_to_be_paid(
    records: Iterable[Mapping[str, object]],
) -> dict[str, dict[str, Decimal]]:
    """
    Build a jurisdiction-level VAT summary from transaction records.

    Expected record fields:
    - jurisdiction: str
    - transaction_type: "sale" or "purchase"
    - one of:
      - vat_amount
      - amount and vat_rate
    """
    jurisdiction_totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for index, record in enumerate(records, start=1):
        jurisdiction = str(record.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Record {index} is missing jurisdiction.")

        transaction_type = str(record.get("transaction_type", "")).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Record {index} has invalid transaction_type '{transaction_type}'. "
                "Use 'sale' or 'purchase'."
            )

        vat_amount = _compute_vat_amount(record)
        if transaction_type == "sale":
            jurisdiction_totals[jurisdiction]["output_vat"] += vat_amount
        else:
            jurisdiction_totals[jurisdiction]["input_vat"] += vat_amount

    summary: dict[str, dict[str, Decimal]] = {}
    for jurisdiction, totals in sorted(jurisdiction_totals.items()):
        output_vat = totals["output_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        input_vat = totals["input_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        vat_to_be_paid = max(output_vat - input_vat, Decimal("0")).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        summary[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_to_be_paid": vat_to_be_paid,
        }

    return summary


def load_transactions_from_csv(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV is missing header row.")
        required = {"jurisdiction", "transaction_type"}
        missing = required.difference(set(reader.fieldnames))
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
        return list(reader)


def _to_jsonable(summary: dict[str, dict[str, Decimal]]) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {key: str(value) for key, value in totals.items()}
        for jurisdiction, totals in summary.items()
    }


def _print_table(summary: dict[str, dict[str, Decimal]]) -> None:
    print(f"{'Jurisdiction':<16} {'Output VAT':>12} {'Input VAT':>12} {'VAT to be paid':>16}")
    print("-" * 60)
    for jurisdiction, totals in summary.items():
        print(
            f"{jurisdiction:<16} "
            f"{totals['output_vat']:>12} "
            f"{totals['input_vat']:>12} "
            f"{totals['vat_to_be_paid']:>16}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument("csv_path", help="Path to a CSV transaction file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary as JSON instead of a formatted table.",
    )
    args = parser.parse_args()

    transactions = load_transactions_from_csv(args.csv_path)
    summary = generate_vat_to_be_paid(transactions)
    if args.json:
        print(json.dumps(_to_jsonable(summary), indent=2))
    else:
        _print_table(summary)


if __name__ == "__main__":
    main()
