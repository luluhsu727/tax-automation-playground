from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping


OUTPUT_DIRECTIONS = {"output", "sale", "sales", "collected"}
INPUT_DIRECTIONS = {"input", "purchase", "purchases", "deductible"}


@dataclass(frozen=True)
class VatSummary:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    vat_to_be_paid: Decimal
    vat_credit: Decimal


def _parse_decimal(raw: str, field_name: str) -> Decimal:
    try:
        return Decimal(raw.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal in field '{field_name}': {raw!r}") from exc


def _normalize_direction(raw: str) -> str:
    if raw is None:
        raise ValueError("Missing required field 'tax_direction'.")

    direction = raw.strip().lower()
    if direction in OUTPUT_DIRECTIONS:
        return "output"
    if direction in INPUT_DIRECTIONS:
        return "input"

    raise ValueError(
        f"Unsupported tax_direction value {raw!r}. "
        "Use one of output/sale/sales/collected/input/purchase/purchases/deductible."
    )


def calculate_vat_payable_by_jurisdiction(
    rows: Iterable[Mapping[str, str]],
) -> list[VatSummary]:
    totals: dict[str, dict[str, Decimal]] = {}

    for index, row in enumerate(rows, start=1):
        jurisdiction = (row.get("jurisdiction") or "").strip()
        if not jurisdiction:
            raise ValueError(f"Row {index} is missing required field 'jurisdiction'.")

        direction = _normalize_direction(row.get("tax_direction"))
        vat_amount = _parse_decimal(row.get("vat_amount", ""), "vat_amount")

        if jurisdiction not in totals:
            totals[jurisdiction] = {"output_vat": Decimal("0"), "input_vat": Decimal("0")}

        bucket = totals[jurisdiction]
        if direction == "output":
            bucket["output_vat"] += vat_amount
        else:
            bucket["input_vat"] += vat_amount

    summaries: list[VatSummary] = []
    for jurisdiction in sorted(totals):
        output_vat = totals[jurisdiction]["output_vat"]
        input_vat = totals[jurisdiction]["input_vat"]
        net_vat = output_vat - input_vat
        summaries.append(
            VatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                net_vat=net_vat,
                vat_to_be_paid=max(net_vat, Decimal("0")),
                vat_credit=max(-net_vat, Decimal("0")),
            )
        )

    return summaries


def read_transactions_csv(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_columns = {"jurisdiction", "tax_direction", "vat_amount"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(
                f"Input CSV is missing required columns: {missing_list}. "
                "Expected jurisdiction,tax_direction,vat_amount."
            )
        return [dict(row) for row in reader]


def write_summary_csv(output_path: Path, summaries: Iterable[VatSummary]) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "jurisdiction",
                "output_vat",
                "input_vat",
                "net_vat",
                "vat_to_be_paid",
                "vat_credit",
            ],
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "jurisdiction": summary.jurisdiction,
                    "output_vat": summary.output_vat,
                    "input_vat": summary.input_vat,
                    "net_vat": summary.net_vat,
                    "vat_to_be_paid": summary.vat_to_be_paid,
                    "vat_credit": summary.vat_credit,
                }
            )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction from a transactions CSV."
    )
    parser.add_argument("input_csv", type=Path, help="Path to source transactions CSV file.")
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("vat_payable_by_jurisdiction.csv"),
        help="Path for generated VAT summary CSV file.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    rows = read_transactions_csv(args.input_csv)
    summaries = calculate_vat_payable_by_jurisdiction(rows)
    write_summary_csv(args.output_csv, summaries)

    print(f"Wrote VAT payable summary for {len(summaries)} jurisdictions to {args.output_csv}")


if __name__ == "__main__":
    main()
