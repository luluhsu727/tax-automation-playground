"""Generate VAT payable totals for each jurisdiction.

This module supports both library usage and CLI usage.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping, Any


TWOPLACES = Decimal("0.01")


@dataclass
class JurisdictionVatSummary:
    """Aggregated VAT totals for one jurisdiction."""

    output_vat: Decimal = Decimal("0")
    input_vat: Decimal = Decimal("0")

    @property
    def net_vat(self) -> Decimal:
        return self.output_vat - self.input_vat

    @property
    def vat_payable(self) -> Decimal:
        return max(self.net_vat, Decimal("0"))

    @property
    def vat_refundable(self) -> Decimal:
        return max(-self.net_vat, Decimal("0"))

    def as_dict(self) -> dict[str, Decimal]:
        return {
            "output_vat": _money(self.output_vat),
            "input_vat": _money(self.input_vat),
            "net_vat": _money(self.net_vat),
            "vat_payable": _money(self.vat_payable),
            "vat_refundable": _money(self.vat_refundable),
        }


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _parse_decimal(value: Any, field_name: str, row_number: int) -> Decimal:
    if value is None or value == "":
        raise ValueError(f"Missing '{field_name}' at row {row_number}")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid '{field_name}' at row {row_number}: {value!r}") from exc


def _normalize_transaction_type(transaction_type: str, row_number: int) -> str:
    normalized = transaction_type.strip().lower()
    if normalized in {"sale", "sales", "output"}:
        return "sale"
    if normalized in {"purchase", "purchases", "input"}:
        return "purchase"
    raise ValueError(
        f"Invalid 'transaction_type' at row {row_number}: {transaction_type!r}. "
        "Expected sale/output or purchase/input."
    )


def _normalize_vat_rate(rate: Decimal) -> Decimal:
    # Accept both fractional rates (0.20) and percentages (20).
    return rate / Decimal("100") if rate > Decimal("1") else rate


def _resolve_vat_amount(row: Mapping[str, Any], row_number: int) -> Decimal:
    vat_amount = row.get("vat_amount")
    if vat_amount not in (None, ""):
        return _parse_decimal(vat_amount, "vat_amount", row_number)

    net_amount = _parse_decimal(row.get("net_amount"), "net_amount", row_number)
    vat_rate = _normalize_vat_rate(_parse_decimal(row.get("vat_rate"), "vat_rate", row_number))
    return net_amount * vat_rate


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Calculate VAT totals grouped by jurisdiction.

    Expected fields per transaction:
    - jurisdiction (required)
    - transaction_type (required): sale/output or purchase/input
    - vat_amount (optional if net_amount + vat_rate provided)
    - net_amount (required if vat_amount omitted)
    - vat_rate (required if vat_amount omitted)
    """

    aggregated: dict[str, JurisdictionVatSummary] = defaultdict(JurisdictionVatSummary)

    for idx, row in enumerate(transactions, start=1):
        jurisdiction = str(row.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError(f"Missing 'jurisdiction' at row {idx}")

        transaction_type = _normalize_transaction_type(
            str(row.get("transaction_type", "")),
            idx,
        )
        vat_amount = _resolve_vat_amount(row, idx)

        summary = aggregated[jurisdiction]
        if transaction_type == "sale":
            summary.output_vat += vat_amount
        else:
            summary.input_vat += vat_amount

    return {jurisdiction: summary.as_dict() for jurisdiction, summary in sorted(aggregated.items())}


def _read_transactions_from_csv(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def _write_csv_output(result: dict[str, dict[str, Decimal]], output_path: Path | None) -> None:
    rows = [
        {
            "jurisdiction": jurisdiction,
            "output_vat": str(summary["output_vat"]),
            "input_vat": str(summary["input_vat"]),
            "net_vat": str(summary["net_vat"]),
            "vat_payable": str(summary["vat_payable"]),
            "vat_refundable": str(summary["vat_refundable"]),
        }
        for jurisdiction, summary in result.items()
    ]
    fieldnames = [
        "jurisdiction",
        "output_vat",
        "input_vat",
        "net_vat",
        "vat_payable",
        "vat_refundable",
    ]

    if output_path is None:
        writer = csv.DictWriter(
            _StdoutWriter(),
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        return

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json_output(result: dict[str, dict[str, Decimal]], output_path: Path | None) -> None:
    payload = {
        jurisdiction: {key: str(value) for key, value in summary.items()}
        for jurisdiction, summary in result.items()
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if output_path is None:
        print(rendered)
        return
    output_path.write_text(rendered + "\n", encoding="utf-8")


class _StdoutWriter:
    """Tiny adapter so csv.DictWriter can write to stdout via print."""

    def write(self, content: str) -> int:
        print(content, end="")
        return len(content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals by jurisdiction from a transaction CSV."
    )
    parser.add_argument("input_csv", type=Path, help="Path to input transaction CSV.")
    parser.add_argument(
        "--format",
        choices=("json", "csv"),
        default="json",
        help="Output format. Defaults to json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    transactions = _read_transactions_from_csv(args.input_csv)
    result = generate_vat_payable_by_jurisdiction(transactions)

    if args.format == "csv":
        _write_csv_output(result, args.output)
    else:
        _write_json_output(result, args.output)


if __name__ == "__main__":
    main()
