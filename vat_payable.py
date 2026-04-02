from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    amount: Decimal
    vat_rate: Decimal
    amount_includes_vat: bool = False


@dataclass
class JurisdictionVatSummary:
    output_vat: Decimal = Decimal("0")
    input_vat: Decimal = Decimal("0")

    @property
    def vat_payable(self) -> Decimal:
        return self.output_vat - self.input_vat


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid {field_name}: {value!r}") from exc


def _normalize_vat_rate(rate: Decimal) -> Decimal:
    if rate < 0:
        raise ValueError("VAT rate must be non-negative.")
    if rate > 1:
        return rate / Decimal("100")
    return rate


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _compute_transaction_vat(amount: Decimal, vat_rate: Decimal, amount_includes_vat: bool) -> Decimal:
    if amount < 0:
        raise ValueError("Amount must be non-negative.")
    if amount_includes_vat:
        vat = amount * vat_rate / (Decimal("1") + vat_rate)
    else:
        vat = amount * vat_rate
    return vat.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction],
) -> dict[str, JurisdictionVatSummary]:
    summaries: dict[str, JurisdictionVatSummary] = {}

    for tx in transactions:
        jurisdiction = tx.jurisdiction.strip()
        if not jurisdiction:
            raise ValueError("Jurisdiction is required.")

        normalized_type = tx.transaction_type.strip().lower()
        if normalized_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type {tx.transaction_type!r}. "
                "Use 'sale' or 'purchase'."
            )

        vat_rate = _normalize_vat_rate(tx.vat_rate)
        vat_amount = _compute_transaction_vat(tx.amount, vat_rate, tx.amount_includes_vat)
        summary = summaries.setdefault(jurisdiction, JurisdictionVatSummary())

        if normalized_type == "sale":
            summary.output_vat += vat_amount
        else:
            summary.input_vat += vat_amount

    for summary in summaries.values():
        summary.output_vat = summary.output_vat.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        summary.input_vat = summary.input_vat.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    return summaries


def _transactions_from_csv(path: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    with path.open(newline="", encoding="utf-8") as file_handle:
        reader = csv.DictReader(file_handle)
        required_columns = {"jurisdiction", "transaction_type", "amount", "vat_rate"}
        if not reader.fieldnames:
            raise ValueError("Input file has no header row.")
        missing_columns = required_columns - set(reader.fieldnames)
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

        for index, row in enumerate(reader, start=2):
            try:
                transactions.append(
                    Transaction(
                        jurisdiction=(row.get("jurisdiction") or "").strip(),
                        transaction_type=(row.get("transaction_type") or "").strip(),
                        amount=_to_decimal(row.get("amount"), "amount"),
                        vat_rate=_to_decimal(row.get("vat_rate"), "vat_rate"),
                        amount_includes_vat=_coerce_bool(row.get("amount_includes_vat")),
                    )
                )
            except ValueError as exc:
                raise ValueError(f"Row {index}: {exc}") from exc
    return transactions


def _write_summary_to_csv(path: Path, summaries: dict[str, JurisdictionVatSummary]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["jurisdiction", "output_vat", "input_vat", "vat_payable"])
        for jurisdiction in sorted(summaries):
            summary = summaries[jurisdiction]
            writer.writerow(
                [
                    jurisdiction,
                    f"{summary.output_vat.quantize(TWOPLACES, rounding=ROUND_HALF_UP):.2f}",
                    f"{summary.input_vat.quantize(TWOPLACES, rounding=ROUND_HALF_UP):.2f}",
                    f"{summary.vat_payable.quantize(TWOPLACES, rounding=ROUND_HALF_UP):.2f}",
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable (output VAT - input VAT) by jurisdiction."
    )
    parser.add_argument("--input", required=True, help="Path to input CSV transactions file.")
    parser.add_argument(
        "--output",
        default="vat_payable_by_jurisdiction.csv",
        help="Path to output CSV file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    transactions = _transactions_from_csv(input_path)
    summaries = compute_vat_payable_by_jurisdiction(transactions)
    _write_summary_to_csv(output_path, summaries)


if __name__ == "__main__":
    main()
