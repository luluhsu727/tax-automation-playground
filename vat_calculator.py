"""Utilities for generating VAT payable totals per jurisdiction."""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None or value == "":
        raise ValueError(f"'{field_name}' is required")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"'{field_name}' must be numeric") from exc


def _record_value(record: Any, field_name: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(field_name)
    return getattr(record, field_name, None)


def _normalize_jurisdiction(value: Any) -> str:
    jurisdiction = str(value or "").strip().upper()
    if not jurisdiction:
        raise ValueError("'jurisdiction' is required")
    return jurisdiction


def _normalize_transaction_type(transaction_type: Any) -> str:
    value = str(transaction_type).strip().lower()
    if value in {"sale", "sales", "output"}:
        return "sale"
    if value in {"purchase", "purchases", "input", "expense"}:
        return "purchase"
    raise ValueError("transaction_type must be either 'sale' or 'purchase'")


def _calculate_vat_amount(record: Any) -> Decimal:
    vat_amount_value = _record_value(record, "vat_amount")
    if vat_amount_value not in (None, ""):
        vat_amount = _to_decimal(vat_amount_value, "vat_amount")
        if vat_amount < 0:
            raise ValueError("'vat_amount' cannot be negative")
        return _quantize(vat_amount)

    net_amount = _to_decimal(_record_value(record, "net_amount"), "net_amount")
    vat_rate = _to_decimal(_record_value(record, "vat_rate"), "vat_rate")
    if vat_rate < 0:
        raise ValueError("'vat_rate' cannot be negative")

    # Accept both decimal rates (0.19) and percentages (19).
    if vat_rate > 1:
        vat_rate = vat_rate / Decimal("100")
    return _quantize(net_amount * vat_rate)


def calculate_vat_payable_by_jurisdiction(
    records: Iterable[Mapping[str, Any] | Any],
) -> dict[str, dict[str, Decimal | str]]:
    """Generate VAT totals grouped by jurisdiction.

    Each input record must include:
      - jurisdiction
      - transaction_type ('sale' or 'purchase')
      - either vat_amount, or net_amount + vat_rate

    Returns:
      Mapping of jurisdiction to:
        - output_vat
        - input_vat
        - net_vat
        - vat_payable
        - vat_credit
        - status
    """
    totals: dict[str, dict[str, Decimal]] = {}

    for index, record in enumerate(records, start=1):
        try:
            jurisdiction = _normalize_jurisdiction(_record_value(record, "jurisdiction"))
            transaction_type = _normalize_transaction_type(
                _record_value(record, "transaction_type")
            )
            vat_amount = _calculate_vat_amount(record)
        except ValueError as exc:
            raise ValueError(f"Invalid record #{index}: {exc}") from exc

        bucket = totals.setdefault(
            jurisdiction,
            {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")},
        )
        if transaction_type == "sale":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    result: dict[str, dict[str, Decimal | str]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _quantize(totals[jurisdiction]["output_vat"])
        input_vat = _quantize(totals[jurisdiction]["input_vat"])
        net_vat = _quantize(output_vat - input_vat)
        vat_payable = _quantize(max(net_vat, Decimal("0.00")))
        vat_credit = _quantize(max(-net_vat, Decimal("0.00")))
        status = "payable" if net_vat > 0 else "credit" if net_vat < 0 else "settled"

        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_payable": vat_payable,
            "vat_credit": vat_credit,
            "status": status,
        }

    return result


def calculate_vat_position_by_jurisdiction(
    records: Iterable[Mapping[str, Any] | Any],
) -> dict[str, dict[str, Decimal | str]]:
    """Compatibility alias for VAT position calculation."""
    return calculate_vat_payable_by_jurisdiction(records)


def generate_vat_to_be_paid_by_jurisdiction(
    records: Iterable[Mapping[str, Any] | Any],
) -> dict[str, Decimal]:
    """Return only VAT payable values per jurisdiction."""
    summary = calculate_vat_payable_by_jurisdiction(records)
    return {
        jurisdiction: values["vat_payable"]  # type: ignore[index]
        for jurisdiction, values in summary.items()
    }


def generate_vat_to_be_paid_for_each_jurisdiction(
    records: Iterable[Mapping[str, Any] | Any],
) -> dict[str, Decimal]:
    """Compatibility alias matching the requested wording."""
    return generate_vat_to_be_paid_by_jurisdiction(records)


def load_records_from_csv(file_path: str | Path) -> list[dict[str, str]]:
    with Path(file_path).open(mode="r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [dict(row) for row in reader]


def _serialize_decimals(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return format(obj, ".2f")
    raise TypeError(f"Cannot serialize type {type(obj)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from CSV input."
    )
    parser.add_argument(
        "csv_file",
        help=(
            "Path to CSV file with columns: jurisdiction, transaction_type, "
            "and either vat_amount or net_amount + vat_rate."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON.",
    )
    args = parser.parse_args()

    records = load_records_from_csv(args.csv_file)
    summary = calculate_vat_payable_by_jurisdiction(records)
    if args.pretty:
        print(json.dumps(summary, default=_serialize_decimals, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, default=_serialize_decimals, sort_keys=True))


if __name__ == "__main__":
    main()
