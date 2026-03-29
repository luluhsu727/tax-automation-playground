from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class VatSummary:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal


def _to_decimal(value: Any, field_name: str) -> Decimal:
    if value is None:
        raise ValueError(f"Missing required numeric field: {field_name}")
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal in field '{field_name}': {value!r}") from exc


def _normalize_transaction_type(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"sale", "sales", "output"}:
        return "sale"
    if normalized in {"purchase", "purchases", "input", "expense"}:
        return "purchase"
    raise ValueError(
        "Unsupported transaction_type. Expected one of "
        "{sale, sales, output, purchase, purchases, input, expense}."
    )


def calculate_vat_payable(
    records: Iterable[Mapping[str, Any]], rounding_scale: str = "0.01"
) -> list[VatSummary]:
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for index, record in enumerate(records, start=1):
        jurisdiction = str(record.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Row {index}: Missing jurisdiction")

        transaction_type = _normalize_transaction_type(record.get("transaction_type"))
        vat_amount_raw = record.get("vat_amount")

        if vat_amount_raw is not None and str(vat_amount_raw).strip() != "":
            vat_amount = _to_decimal(vat_amount_raw, "vat_amount")
        else:
            net_amount = _to_decimal(record.get("net_amount"), "net_amount")
            vat_rate = _to_decimal(record.get("vat_rate"), "vat_rate")
            vat_amount = net_amount * vat_rate

        if transaction_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    quantizer = Decimal(rounding_scale)
    summaries: list[VatSummary] = []
    for jurisdiction in sorted(totals):
        output_vat = totals[jurisdiction]["output_vat"].quantize(
            quantizer, rounding=ROUND_HALF_UP
        )
        input_vat = totals[jurisdiction]["input_vat"].quantize(
            quantizer, rounding=ROUND_HALF_UP
        )
        summaries.append(
            VatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                vat_payable=(output_vat - input_vat).quantize(
                    quantizer, rounding=ROUND_HALF_UP
                ),
            )
        )

    return summaries


def read_transactions_csv(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("Input CSV is missing headers.")
        return list(reader)


def write_vat_summary_csv(output_path: Path, summaries: Iterable[VatSummary]) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["jurisdiction", "output_vat", "input_vat", "vat_payable"],
        )
        writer.writeheader()
        for summary in summaries:
            writer.writerow(
                {
                    "jurisdiction": summary.jurisdiction,
                    "output_vat": f"{summary.output_vat:.2f}",
                    "input_vat": f"{summary.input_vat:.2f}",
                    "vat_payable": f"{summary.vat_payable:.2f}",
                }
            )


def generate_vat_payable(input_csv: Path, output_csv: Path) -> list[VatSummary]:
    records = read_transactions_csv(input_csv)
    summaries = calculate_vat_payable(records)
    write_vat_summary_csv(output_csv, summaries)
    return summaries


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals per jurisdiction from transaction CSV."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to transaction CSV.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path where VAT payable CSV should be written.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    summaries = generate_vat_payable(args.input, args.output)
    print(f"Generated VAT summary for {len(summaries)} jurisdiction(s): {args.output}")


if __name__ == "__main__":
    main()
