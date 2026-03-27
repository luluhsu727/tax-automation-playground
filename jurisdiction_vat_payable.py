"""Jurisdiction VAT payable helpers with CSV support."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from vat_core import VatError, money, normalize_jurisdiction, to_decimal, to_rate


DEFAULT_VAT_RATES: dict[str, Decimal] = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}


def _resolve_column(fieldnames: Iterable[str], candidates: tuple[str, ...]) -> str:
    normalized = {name.lower(): name for name in fieldnames}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    raise ValueError(f"Missing required CSV column. Expected one of: {candidates}")


def load_transactions(path: Path) -> list[dict[str, Decimal | str | None]]:
    """Load transaction rows from CSV using flexible column names."""
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
            jurisdiction = normalize_jurisdiction(row.get(jurisdiction_col, ""))
            taxable_amount = to_decimal(row.get(taxable_col, ""), field_name=taxable_col)

            vat_rate: Decimal | None
            raw_rate = row.get(vat_rate_col, "") if vat_rate_col else ""
            if raw_rate in ("", None):
                vat_rate = None
            else:
                vat_rate = to_rate(raw_rate, field_name=vat_rate_col)

            records.append(
                {
                    "jurisdiction": jurisdiction,
                    "taxable_amount": taxable_amount,
                    "vat_rate": vat_rate,
                }
            )
        return records


def _resolve_tx_rate(jurisdiction: str, raw_rate: Any) -> Decimal:
    if raw_rate is None:
        if jurisdiction not in DEFAULT_VAT_RATES:
            raise ValueError(f"No VAT rate supplied for jurisdiction '{jurisdiction}'")
        return DEFAULT_VAT_RATES[jurisdiction]
    return to_rate(raw_rate, field_name="vat_rate")


def compute_vat_payable_by_jurisdiction(
    transactions: list[dict[str, Decimal | str | None]],
) -> list[dict[str, str]]:
    """Build summary rows with total taxable and total VAT payable."""
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"taxable": Decimal("0.00"), "vat": Decimal("0.00")}
    )
    for tx in transactions:
        jurisdiction = normalize_jurisdiction(tx.get("jurisdiction"))
        taxable_amount = to_decimal(tx.get("taxable_amount"), field_name="taxable_amount")
        vat_rate = _resolve_tx_rate(jurisdiction, tx.get("vat_rate"))

        totals[jurisdiction]["taxable"] += taxable_amount
        totals[jurisdiction]["vat"] += money(taxable_amount * vat_rate)

    summary: list[dict[str, str]] = []
    for jurisdiction in sorted(totals):
        taxable_total = money(totals[jurisdiction]["taxable"])
        vat_total = money(totals[jurisdiction]["vat"])
        effective_rate = Decimal("0.00")
        if taxable_total != 0:
            effective_rate = vat_total / taxable_total

        summary.append(
            {
                "jurisdiction": jurisdiction,
                "total_taxable_amount": f"{taxable_total:.2f}",
                "total_vat_payable": f"{vat_total:.2f}",
                "effective_vat_rate": f"{effective_rate:.2f}",
            }
        )
    return summary


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: list[dict[str, Decimal | str | None]],
) -> dict[str, Decimal]:
    """Generate VAT to be paid totals by jurisdiction."""
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for tx in transactions:
        jurisdiction = normalize_jurisdiction(tx.get("jurisdiction"))
        taxable_amount = to_decimal(tx.get("taxable_amount"), field_name="taxable_amount")
        vat_rate = _resolve_tx_rate(jurisdiction, tx.get("vat_rate"))
        totals[jurisdiction] += money(taxable_amount * vat_rate)
    return {jurisdiction: money(amount) for jurisdiction, amount in sorted(totals.items())}


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
    try:
        main()
    except VatError as exc:
        raise SystemExit(str(exc))
