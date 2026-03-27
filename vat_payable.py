from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal

    @property
    def vat_amount(self) -> Decimal:
        return (self.net_amount * self.vat_rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class JurisdictionVatSummary:
    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    payable_vat: Decimal
    refundable_vat: Decimal


def _clean_jurisdiction(value: str) -> str:
    cleaned = value.strip().upper()
    if not cleaned:
        raise ValueError("jurisdiction cannot be empty")
    return cleaned


def _clean_transaction_type(value: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in {"sale", "purchase"}:
        raise ValueError("transaction_type must be either 'sale' or 'purchase'")
    return cleaned


def _parse_decimal(value: str, field: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"invalid decimal value for {field}: {value!r}") from exc


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> list[JurisdictionVatSummary]:
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for tx in transactions:
        vat_amount = tx.vat_amount
        jurisdiction = _clean_jurisdiction(tx.jurisdiction)
        tx_type = _clean_transaction_type(tx.transaction_type)

        if tx_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    summaries: list[JurisdictionVatSummary] = []
    for jurisdiction in sorted(totals):
        output_vat = totals[jurisdiction]["output_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        input_vat = totals[jurisdiction]["input_vat"].quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        net_vat = (output_vat - input_vat).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        payable_vat = max(net_vat, Decimal("0")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        refundable_vat = max(-net_vat, Decimal("0")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

        summaries.append(
            JurisdictionVatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                net_vat=net_vat,
                payable_vat=payable_vat,
                refundable_vat=refundable_vat,
            )
        )

    return summaries


def read_transactions_from_csv(input_path: Path) -> list[Transaction]:
    with input_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"jurisdiction", "transaction_type", "net_amount", "vat_rate"}
        missing = required.difference(reader.fieldnames or set())
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"missing required input column(s): {missing_list}")

        transactions: list[Transaction] = []
        for idx, row in enumerate(reader, start=2):
            try:
                transactions.append(
                    Transaction(
                        jurisdiction=_clean_jurisdiction(row["jurisdiction"]),
                        transaction_type=_clean_transaction_type(row["transaction_type"]),
                        net_amount=_parse_decimal(row["net_amount"], "net_amount"),
                        vat_rate=_parse_decimal(row["vat_rate"], "vat_rate"),
                    )
                )
            except Exception as exc:
                raise ValueError(f"invalid data at CSV line {idx}: {exc}") from exc
    return transactions


def write_summary_to_csv(output_path: Path, summary: Iterable[JurisdictionVatSummary]) -> None:
    fieldnames = [
        "jurisdiction",
        "output_vat",
        "input_vat",
        "net_vat",
        "payable_vat",
        "refundable_vat",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary:
            writer.writerow(
                {
                    "jurisdiction": row.jurisdiction,
                    "output_vat": str(row.output_vat),
                    "input_vat": str(row.input_vat),
                    "net_vat": str(row.net_vat),
                    "payable_vat": str(row.payable_vat),
                    "refundable_vat": str(row.refundable_vat),
                }
            )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction CSV data."
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to input transactions CSV")
    parser.add_argument(
        "--output", required=True, type=Path, help="Path where jurisdiction VAT CSV is written"
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    transactions = read_transactions_from_csv(args.input)
    summary = calculate_vat_payable_by_jurisdiction(transactions)
    write_summary_to_csv(args.output, summary)


if __name__ == "__main__":
    main()
