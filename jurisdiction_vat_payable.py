"""Jurisdiction VAT payable helpers with CSV support."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable


MONEY = Decimal("0.01")
DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _parse_decimal(raw_value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(raw_value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid decimal value for {field_name}: {raw_value!r}") from exc


def _resolve_column(fieldnames: Iterable[str], candidates: tuple[str, ...]) -> str:
    normalized = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    raise ValueError(f"Missing required CSV column. Expected one of: {candidates}")


def load_transactions(path: Path) -> list[dict[str, Decimal | str | None]]:
    with path.open("r", newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("Input CSV has no header row.")

        jurisdiction_col = _resolve_column(fieldnames, ("jurisdiction", "country"))
        taxable_col = _resolve_column(fieldnames, ("taxable_amount", "revenue", "net_amount"))
        vat_rate_col = ""
        try:
            vat_rate_col = _resolve_column(fieldnames, ("vat_rate", "tax_rate"))
        except ValueError:
            vat_rate_col = ""

        records: list[dict[str, Decimal | str | None]] = []
        for row in reader:
            jurisdiction = str(row.get(jurisdiction_col, "")).strip().upper()
            if not jurisdiction:
                raise ValueError("Encountered row with empty jurisdiction/country value.")
            taxable_amount = _parse_decimal(row.get(taxable_col, ""), taxable_col)
            vat_rate: Decimal | None
            raw_rate = row.get(vat_rate_col, "") if vat_rate_col else ""
            if raw_rate in ("", None):
                vat_rate = None
            else:
                vat_rate = _parse_decimal(raw_rate, vat_rate_col)
                if vat_rate > 1:
                    vat_rate = vat_rate / Decimal("100")
            records.append(
                {
                    "jurisdiction": jurisdiction,
                    "taxable_amount": taxable_amount,
                    "vat_rate": vat_rate,
                }
            )
        return records


def compute_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Decimal | str | None]],
) -> list[dict[str, str]]:
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"taxable": Decimal("0.00"), "vat": Decimal("0.00")}
    )
    for tx in transactions:
        jurisdiction = str(tx["jurisdiction"]).upper()
        taxable_amount = _parse_decimal(tx["taxable_amount"], "taxable_amount")
        raw_rate = tx.get("vat_rate")
        if raw_rate is None:
            if jurisdiction not in DEFAULT_VAT_RATES:
                raise ValueError(f"No VAT rate supplied for jurisdiction '{jurisdiction}'")
            vat_rate = DEFAULT_VAT_RATES[jurisdiction]
        else:
            vat_rate = _parse_decimal(raw_rate, "vat_rate")
            if vat_rate > 1:
                vat_rate = vat_rate / Decimal("100")

        totals[jurisdiction]["taxable"] += taxable_amount
        totals[jurisdiction]["vat"] += _money(taxable_amount * vat_rate)

    summary: list[dict[str, str]] = []
    for jurisdiction in sorted(totals):
        taxable_total = _money(totals[jurisdiction]["taxable"])
        vat_total = _money(totals[jurisdiction]["vat"])
        effective_rate = (
            vat_total / taxable_total if taxable_total != 0 else Decimal("0.00")
        )
        # Keep two-decimal formatting for amounts; keep rate in canonical VAT style.
        summary.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{vat_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}".rstrip("0").rstrip("."),
            }
        )
    return summary


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: list[dict[str, Decimal | str | None]],
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for tx in transactions:
        jurisdiction = str(tx["jurisdiction"]).upper()
        taxable_amount = _parse_decimal(tx["taxable_amount"], "taxable_amount")
        raw_rate = tx.get("vat_rate")
        if raw_rate is None:
            if jurisdiction not in DEFAULT_VAT_RATES:
                raise ValueError(f"No VAT rate supplied for jurisdiction '{jurisdiction}'")
            vat_rate = DEFAULT_VAT_RATES[jurisdiction]
        else:
            vat_rate = _parse_decimal(raw_rate, "vat_rate")
            if vat_rate > 1:
                vat_rate = vat_rate / Decimal("100")
        totals[jurisdiction] += _money(taxable_amount * vat_rate)

    return {jurisdiction: _money(amount) for jurisdiction, amount in sorted(totals.items())}


def write_summary(path: Path, summary_rows: list[dict[str, str]]) -> None:
    fields = [
        "jurisdiction",
        "total_taxable_amount",
        "total_vat_payable",
        "effective_vat_rate",
    ]
    with path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument("--input", required=True, help="Path to source CSV.")
    parser.add_argument(
        "--output",
        default="jurisdiction_vat_payable.csv",
        help="Path to summary CSV output.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    transactions = load_transactions(input_path)
    summary = compute_vat_payable_by_jurisdiction(transactions)
    write_summary(output_path, summary)
    print(f"Wrote VAT payable summary to: {output_path}")


if __name__ == "__main__":
    main()
