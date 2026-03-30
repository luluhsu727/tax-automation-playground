#!/usr/bin/env python3
"""Generate VAT to be paid for each jurisdiction."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")

DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}

JURISDICTION_KEYS = ("jurisdiction", "country")
AMOUNT_KEYS = ("amount", "taxable_amount", "net_amount", "revenue")
VAT_RATE_KEYS = ("vat_rate", "rate")
TRANSACTION_TYPE_KEYS = ("type", "transaction_type", "tax_direction")
SALE_TYPES = {"sale", "output", "collected", "credit"}
PURCHASE_TYPES = {"purchase", "input", "paid", "debit"}


class VatComputationError(ValueError):
    """Raised when VAT data is invalid."""


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _to_decimal(raw_value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - defensive branch
        raise VatComputationError(
            f"Invalid decimal value for '{field_name}': {raw_value}"
        ) from exc


def _read_value(data: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    lowered = {str(key).lower(): key for key in data}
    for key in keys:
        if key in lowered:
            return data[lowered[key]]
    return None


def _normalize_jurisdiction(raw: Any) -> str:
    jurisdiction = str(raw or "").strip().upper()
    if not jurisdiction:
        raise VatComputationError("Jurisdiction cannot be empty")
    return jurisdiction


def _normalize_transaction_type(raw: Any) -> str:
    if raw is None:
        return "sale"
    normalized = str(raw).strip().lower()
    if normalized in SALE_TYPES:
        return "sale"
    if normalized in PURCHASE_TYPES:
        return "purchase"
    raise VatComputationError(f"Unsupported transaction type: {raw}")


def _normalize_vat_rate(raw_rate: Any, jurisdiction: str) -> Decimal:
    if raw_rate is None or str(raw_rate).strip() == "":
        if jurisdiction not in DEFAULT_VAT_RATES:
            raise VatComputationError(
                f"No VAT rate supplied for jurisdiction '{jurisdiction}'"
            )
        return DEFAULT_VAT_RATES[jurisdiction]

    vat_rate = _to_decimal(raw_rate, "vat_rate")
    if vat_rate < 0:
        raise VatComputationError("VAT rate cannot be negative")
    if vat_rate > 1:
        vat_rate = vat_rate / Decimal("100")
    return vat_rate


def _normalize_transaction(raw: Mapping[str, Any]) -> tuple[str, str, Decimal, Decimal]:
    jurisdiction = _normalize_jurisdiction(_read_value(raw, JURISDICTION_KEYS))

    amount_raw = _read_value(raw, AMOUNT_KEYS)
    amount = _to_decimal(amount_raw, "amount")
    if amount < 0:
        raise VatComputationError("Amount cannot be negative")

    vat_rate_raw = _read_value(raw, VAT_RATE_KEYS)
    vat_rate = _normalize_vat_rate(vat_rate_raw, jurisdiction)

    transaction_type_raw = _read_value(raw, TRANSACTION_TYPE_KEYS)
    transaction_type = _normalize_transaction_type(transaction_type_raw)
    return jurisdiction, transaction_type, amount, vat_rate


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """
    Calculate VAT by jurisdiction.

    Returns a dict per jurisdiction with:
      - output_vat: VAT on sales
      - input_vat: VAT on purchases
      - vat_payable: output_vat - input_vat
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for raw in transactions:
        jurisdiction, transaction_type, amount, vat_rate = _normalize_transaction(raw)
        vat_amount = amount * vat_rate
        if transaction_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    results: dict[str, dict[str, float]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _money(totals[jurisdiction]["output_vat"])
        input_vat = _money(totals[jurisdiction]["input_vat"])
        vat_payable = _money(output_vat - input_vat)
        results[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }
    return results


def vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """Return VAT payable amount for each jurisdiction."""
    result = calculate_vat_payable_by_jurisdiction(transactions)
    return {jurisdiction: values["vat_payable"] for jurisdiction, values in result.items()}


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """Compatibility alias for VAT payable amount by jurisdiction."""
    return vat_payable_by_jurisdiction(transactions)


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    """Compatibility alias for VAT payable amount by jurisdiction."""
    return vat_payable_by_jurisdiction(transactions)


def generate_vat_summary_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """Compatibility alias for the detailed VAT summary."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def calculate_vat_position_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """Compatibility alias for the detailed VAT summary."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def generate_vat_payable_per_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """Compatibility alias for the detailed VAT summary."""
    return calculate_vat_payable_by_jurisdiction(transactions)


def _load_transactions_json(input_path: Path) -> list[dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise VatComputationError("Input JSON must contain a list of transactions")
    return payload


def _load_transactions_csv(input_path: Path) -> list[dict[str, Any]]:
    with input_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise VatComputationError("Input CSV has no header row")
        return [dict(row) for row in reader]


def load_transactions(path: str | Path) -> list[dict[str, Any]]:
    """Load transactions from JSON or CSV."""
    input_path = Path(path)
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        return _load_transactions_json(input_path)
    if suffix == ".csv":
        return _load_transactions_csv(input_path)
    raise VatComputationError("Unsupported input file format; use .json or .csv")


def _write_csv_report(output_path: Path, vat_data: Mapping[str, Mapping[str, float]]) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jurisdiction", "output_vat", "input_vat", "vat_payable"])
        for jurisdiction in sorted(vat_data):
            values = vat_data[jurisdiction]
            writer.writerow(
                [
                    jurisdiction,
                    f"{values['output_vat']:.2f}",
                    f"{values['input_vat']:.2f}",
                    f"{values['vat_payable']:.2f}",
                ]
            )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the VAT to be paid for each jurisdiction."
    )
    parser.add_argument("input_file", help="Input transactions file (.json or .csv)")
    parser.add_argument(
        "--output-csv",
        default="vat_payable_by_jurisdiction.csv",
        help="CSV output path",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    transactions = load_transactions(args.input_file)
    vat_data = calculate_vat_payable_by_jurisdiction(transactions)
    _write_csv_report(Path(args.output_csv), vat_data)
    print(json.dumps(vat_data, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
