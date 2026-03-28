#!/usr/bin/env python3
"""Utilities to generate VAT payable for each jurisdiction."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")

# Common defaults used when per-transaction rates are omitted.
DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}

JURISDICTION_COLUMNS = ("jurisdiction", "country")
TAXABLE_AMOUNT_COLUMNS = ("taxable_amount", "net_amount", "revenue", "amount")
VAT_RATE_COLUMNS = ("vat_rate", "rate")
TRANSACTION_TYPE_COLUMNS = ("transaction_type", "type")


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _parse_decimal(raw_value: Any, field_name: str) -> Decimal:
    if raw_value is None:
        raise ValueError(f"Missing decimal value for '{field_name}'.")
    try:
        return Decimal(str(raw_value).strip())
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal value for '{field_name}': {raw_value}") from exc


def _normalize_jurisdiction(raw_value: Any) -> str:
    jurisdiction = str(raw_value or "").strip().upper()
    if not jurisdiction:
        raise ValueError("Each transaction must include a non-empty jurisdiction.")
    return jurisdiction


def _resolve_column(fieldnames: Iterable[str], candidates: tuple[str, ...]) -> str:
    lookup = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    raise ValueError(f"Missing required column. Expected one of: {', '.join(candidates)}")


def _get_optional_column(
    fieldnames: Iterable[str], candidates: tuple[str, ...]
) -> str | None:
    lookup = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def _extract_value(row: Mapping[str, Any], candidates: tuple[str, ...]) -> Any:
    lowered = {str(key).lower(): value for key, value in row.items()}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _resolve_vat_rate(jurisdiction: str, vat_rate_value: Any) -> Decimal:
    vat_rate = None
    if vat_rate_value not in (None, ""):
        vat_rate = _parse_decimal(vat_rate_value, "vat_rate")

    if vat_rate is None:
        if jurisdiction not in DEFAULT_VAT_RATES:
            raise ValueError(
                f"No VAT rate supplied for jurisdiction '{jurisdiction}', "
                "and no default rate is configured."
            )
        vat_rate = DEFAULT_VAT_RATES[jurisdiction]
    elif vat_rate > 1:
        # Support percent input (e.g. 19 for 19%).
        vat_rate = vat_rate / Decimal("100")
    return vat_rate


def load_transactions(path: str | Path) -> list[dict[str, Decimal | str | None]]:
    """Load transaction rows from CSV and normalize fields."""
    input_path = Path(path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")

        jurisdiction_col = _resolve_column(reader.fieldnames, JURISDICTION_COLUMNS)
        taxable_col = _resolve_column(reader.fieldnames, TAXABLE_AMOUNT_COLUMNS)
        vat_rate_col = _get_optional_column(reader.fieldnames, VAT_RATE_COLUMNS)
        transaction_type_col = _get_optional_column(
            reader.fieldnames, TRANSACTION_TYPE_COLUMNS
        )

        transactions: list[dict[str, Decimal | str | None]] = []
        for idx, row in enumerate(reader, start=2):
            jurisdiction = str(row.get(jurisdiction_col, "")).strip().upper()
            if not jurisdiction:
                raise ValueError(f"Missing jurisdiction value on row {idx}.")

            taxable_amount = _parse_decimal(row.get(taxable_col, ""), taxable_col)

            vat_rate: Decimal | None = None
            if vat_rate_col:
                raw_rate = str(row.get(vat_rate_col, "")).strip()
                if raw_rate:
                    vat_rate = _parse_decimal(raw_rate, vat_rate_col)

            transaction_type = "sale"
            if transaction_type_col:
                value = str(row.get(transaction_type_col, "")).strip().lower()
                if value:
                    transaction_type = value

            transactions.append(
                {
                    "jurisdiction": jurisdiction,
                    "taxable_amount": taxable_amount,
                    "amount": taxable_amount,
                    "vat_rate": vat_rate,
                    "transaction_type": transaction_type,
                }
            )

    return transactions


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Aggregate VAT payable totals by jurisdiction using sale-side VAT."""
    totals: dict[str, dict[str, Decimal]] = {}

    for row in transactions:
        jurisdiction = _normalize_jurisdiction(_extract_value(row, JURISDICTION_COLUMNS))
        taxable_amount = _parse_decimal(
            _extract_value(row, TAXABLE_AMOUNT_COLUMNS), "taxable_amount"
        )
        vat_rate = _resolve_vat_rate(
            jurisdiction,
            _extract_value(row, VAT_RATE_COLUMNS),
        )

        vat_payable = _money(taxable_amount * vat_rate)
        if jurisdiction not in totals:
            totals[jurisdiction] = {
                "total_taxable_amount": Decimal("0.00"),
                "total_vat_payable": Decimal("0.00"),
            }
        totals[jurisdiction]["total_taxable_amount"] += taxable_amount
        totals[jurisdiction]["total_vat_payable"] += vat_payable

    summary_rows: list[dict[str, str]] = []
    for jurisdiction in sorted(totals):
        taxable_total = _money(totals[jurisdiction]["total_taxable_amount"])
        payable_total = _money(totals[jurisdiction]["total_vat_payable"])
        effective_rate = (
            _money(payable_total / taxable_total)
            if taxable_total != Decimal("0.00")
            else Decimal("0.00")
        )
        summary_rows.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{payable_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}",
            }
        )

    return summary_rows


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Return only VAT-to-be-paid totals keyed by jurisdiction."""
    summary = compute_vat_payable_by_jurisdiction(transactions)
    return {row["jurisdiction"]: Decimal(row["total_vat_payable"]) for row in summary}


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, float]]:
    """
    Calculate output VAT, input VAT, and net VAT payable per jurisdiction.

    Supported transaction types:
    - sale: contributes to output VAT
    - purchase: contributes to input VAT
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "output_vat": Decimal("0.00"),
            "input_vat": Decimal("0.00"),
        }
    )

    for row in transactions:
        jurisdiction = _normalize_jurisdiction(_extract_value(row, JURISDICTION_COLUMNS))
        amount = _parse_decimal(_extract_value(row, TAXABLE_AMOUNT_COLUMNS), "amount")
        vat_rate = _resolve_vat_rate(
            jurisdiction,
            _extract_value(row, VAT_RATE_COLUMNS),
        )
        vat_amount = _money(amount * vat_rate)

        tx_type = str(_extract_value(row, TRANSACTION_TYPE_COLUMNS) or "sale").strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(f"Unsupported transaction type: {tx_type}")

        if tx_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    result: dict[str, dict[str, float]] = {}
    for jurisdiction in sorted(totals):
        output_vat = _money(totals[jurisdiction]["output_vat"])
        input_vat = _money(totals[jurisdiction]["input_vat"])
        vat_payable = _money(output_vat - input_vat)
        result[jurisdiction] = {
            "output_vat": float(output_vat),
            "input_vat": float(input_vat),
            "vat_payable": float(vat_payable),
        }
    return result


def write_summary(path: str | Path, summary_rows: list[dict[str, str]]) -> None:
    """Write jurisdiction-level VAT payable summary CSV."""
    output_path = Path(path)
    fieldnames = (
        "jurisdiction",
        "total_taxable_amount",
        "total_vat_payable",
        "effective_vat_rate",
    )
    with output_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def _read_transactions(path: str | Path) -> list[dict[str, Any]]:
    input_path = Path(path)
    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        return load_transactions(input_path)
    if suffix == ".json":
        with input_path.open("r", encoding="utf-8") as infile:
            payload = json.load(infile)
        if not isinstance(payload, list):
            raise ValueError("Input JSON must be an array of transaction objects.")
        return payload
    raise ValueError("Unsupported input format. Use .csv or .json.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the VAT to be paid for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input transactions file path (.csv or .json).",
    )
    parser.add_argument(
        "--output",
        default="vat_payable_by_jurisdiction.csv",
        help="Output CSV path for jurisdiction summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    transactions = _read_transactions(args.input)
    summary_rows = compute_vat_payable_by_jurisdiction(transactions)
    write_summary(args.output, summary_rows)
    print(f"Wrote {len(summary_rows)} jurisdiction rows to {args.output}")


if __name__ == "__main__":
    main()
