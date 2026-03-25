"""VAT calculation primitives and CSV helpers."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import csv
from pathlib import Path
from typing import Iterable


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class VATTransaction:
    """Represents a taxable transaction used in VAT reporting."""

    jurisdiction: str
    transaction_type: str
    net_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal | None = None

    def resolved_vat_amount(self) -> Decimal:
        """Return explicit VAT amount when present, otherwise derive it."""
        if self.vat_amount is not None:
            return self.vat_amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        return (self.net_amount * self.vat_rate).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """Aggregated VAT values for a single jurisdiction."""

    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal
    transaction_count: int


def _parse_decimal(raw_value: str, field_name: str) -> Decimal:
    try:
        return Decimal(raw_value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal in field '{field_name}': {raw_value}") from exc


def _normalize_transaction_type(raw_transaction_type: str) -> str:
    normalized = raw_transaction_type.strip().lower()
    if normalized not in {"sale", "purchase"}:
        raise ValueError(
            "transaction_type must be either 'sale' or 'purchase', "
            f"got: {raw_transaction_type!r}"
        )
    return normalized


def summarize_vat_by_jurisdiction(
    transactions: Iterable[VATTransaction],
) -> dict[str, JurisdictionVatSummary]:
    """Aggregate output/input VAT and compute payable amount per jurisdiction."""
    output_vat_by_jurisdiction: dict[str, Decimal] = {}
    input_vat_by_jurisdiction: dict[str, Decimal] = {}
    transaction_count_by_jurisdiction: dict[str, int] = {}

    for tx in transactions:
        jurisdiction = tx.jurisdiction.strip()
        if not jurisdiction:
            raise ValueError("jurisdiction is required and cannot be empty")

        tx_type = _normalize_transaction_type(tx.transaction_type)
        vat_amount = tx.resolved_vat_amount()

        if tx_type == "sale":
            output_vat_by_jurisdiction[jurisdiction] = (
                output_vat_by_jurisdiction.get(jurisdiction, Decimal("0")) + vat_amount
            )
            input_vat_by_jurisdiction.setdefault(jurisdiction, Decimal("0"))
        else:
            input_vat_by_jurisdiction[jurisdiction] = (
                input_vat_by_jurisdiction.get(jurisdiction, Decimal("0")) + vat_amount
            )
            output_vat_by_jurisdiction.setdefault(jurisdiction, Decimal("0"))

        transaction_count_by_jurisdiction[jurisdiction] = (
            transaction_count_by_jurisdiction.get(jurisdiction, 0) + 1
        )

    jurisdictions = sorted(
        set(output_vat_by_jurisdiction)
        | set(input_vat_by_jurisdiction)
        | set(transaction_count_by_jurisdiction)
    )

    summary: dict[str, JurisdictionVatSummary] = {}
    for jurisdiction in jurisdictions:
        output_vat = output_vat_by_jurisdiction.get(jurisdiction, Decimal("0")).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        input_vat = input_vat_by_jurisdiction.get(jurisdiction, Decimal("0")).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        vat_payable = (output_vat - input_vat).quantize(
            TWOPLACES, rounding=ROUND_HALF_UP
        )
        summary[jurisdiction] = JurisdictionVatSummary(
            jurisdiction=jurisdiction,
            output_vat=output_vat,
            input_vat=input_vat,
            vat_payable=vat_payable,
            transaction_count=transaction_count_by_jurisdiction.get(jurisdiction, 0),
        )

    return summary


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[VATTransaction],
) -> dict[str, Decimal]:
    """Return VAT payable amount per jurisdiction."""
    summary = summarize_vat_by_jurisdiction(transactions)
    return {jurisdiction: row.vat_payable for jurisdiction, row in summary.items()}


def load_transactions_from_csv(path: str | Path) -> list[VATTransaction]:
    """Load transactions from CSV.

    Expected headers:
    - jurisdiction
    - transaction_type (sale|purchase)
    - net_amount
    - vat_rate (0.20 for 20%)
    - vat_amount (optional; when blank, derived from net_amount * vat_rate)
    """
    csv_path = Path(path)
    transactions: list[VATTransaction] = []

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"jurisdiction", "transaction_type", "net_amount", "vat_rate"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "CSV is missing required headers: " + ", ".join(sorted(missing))
            )

        for row in reader:
            raw_vat_amount = (row.get("vat_amount") or "").strip()
            transactions.append(
                VATTransaction(
                    jurisdiction=(row.get("jurisdiction") or "").strip(),
                    transaction_type=(row.get("transaction_type") or "").strip(),
                    net_amount=_parse_decimal(row.get("net_amount", ""), "net_amount"),
                    vat_rate=_parse_decimal(row.get("vat_rate", ""), "vat_rate"),
                    vat_amount=(
                        _parse_decimal(raw_vat_amount, "vat_amount")
                        if raw_vat_amount
                        else None
                    ),
                )
            )

    return transactions
