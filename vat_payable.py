from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class JurisdictionVatTotals:
    output_vat: Decimal
    input_vat: Decimal
    vat_to_be_paid: Decimal


def _to_decimal(value: Any, field_name: str, transaction_idx: int) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(
            f"Transaction {transaction_idx}: invalid {field_name!r} value {value!r}"
        ) from exc


def _quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_rate(vat_rate: Decimal) -> Decimal:
    """Accept VAT rates as fractions (0.20) or percentages (20)."""
    if vat_rate > 1:
        return (vat_rate / Decimal("100")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
    return vat_rate


def _extract_vat_amount(transaction: Mapping[str, Any], transaction_idx: int) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount", transaction_idx)
        if vat_amount < 0:
            raise ValueError(
                f"Transaction {transaction_idx}: vat_amount cannot be negative"
            )
        return _quantize_money(vat_amount)

    if "net_amount" not in transaction or "vat_rate" not in transaction:
        raise ValueError(
            f"Transaction {transaction_idx}: include vat_amount or both "
            "net_amount and vat_rate"
        )

    net_amount = _to_decimal(transaction["net_amount"], "net_amount", transaction_idx)
    vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate", transaction_idx)

    if net_amount < 0:
        raise ValueError(f"Transaction {transaction_idx}: net_amount cannot be negative")
    if vat_rate < 0:
        raise ValueError(f"Transaction {transaction_idx}: vat_rate cannot be negative")

    vat_amount = net_amount * _normalize_rate(vat_rate)
    return _quantize_money(vat_amount)


def generate_vat_to_be_paid(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, JurisdictionVatTotals]:
    """
    Compute VAT totals per jurisdiction from transaction entries.

    Transaction shape:
    - jurisdiction: str (required)
    - transaction_type: "sale" | "purchase" (required)
    - vat_amount: number-like (optional)
    - net_amount: number-like (required when vat_amount missing)
    - vat_rate: number-like rate e.g. 0.20 or 20 (required when vat_amount missing)

    A "sale" adds to output VAT and a "purchase" adds to input VAT.
    VAT to be paid = output VAT - input VAT.
    """
    working: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for idx, transaction in enumerate(transactions):
        if not isinstance(transaction, Mapping):
            raise ValueError(f"Transaction {idx}: expected mapping, got {type(transaction)}")

        jurisdiction = transaction.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(f"Transaction {idx}: jurisdiction must be a non-empty string")
        jurisdiction = jurisdiction.strip()

        transaction_type = str(transaction.get("transaction_type", "")).strip().lower()
        if transaction_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Transaction {idx}: transaction_type must be 'sale' or 'purchase'"
            )

        vat_amount = _extract_vat_amount(transaction, idx)

        if transaction_type == "sale":
            working[jurisdiction]["output_vat"] += vat_amount
        else:
            working[jurisdiction]["input_vat"] += vat_amount

    results: dict[str, JurisdictionVatTotals] = {}
    for jurisdiction in sorted(working):
        output_vat = _quantize_money(working[jurisdiction]["output_vat"])
        input_vat = _quantize_money(working[jurisdiction]["input_vat"])
        vat_to_be_paid = _quantize_money(output_vat - input_vat)
        results[jurisdiction] = JurisdictionVatTotals(
            output_vat=output_vat,
            input_vat=input_vat,
            vat_to_be_paid=vat_to_be_paid,
        )
    return results


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Compatibility wrapper returning VAT payable only."""
    full = generate_vat_to_be_paid(transactions)
    return {jurisdiction: totals.vat_to_be_paid for jurisdiction, totals in full.items()}


def generate_vat_to_be_paid_from_json(
    input_path: str | Path,
) -> dict[str, JurisdictionVatTotals]:
    with Path(input_path).open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transactions")

    return generate_vat_to_be_paid(payload)


def _format_report(vat_by_jurisdiction: Mapping[str, JurisdictionVatTotals]) -> str:
    header = "jurisdiction,output_vat,input_vat,vat_to_be_paid"
    rows = [header]
    for jurisdiction, totals in vat_by_jurisdiction.items():
        rows.append(
            f"{jurisdiction},{totals.output_vat},{totals.input_vat},{totals.vat_to_be_paid}"
        )
    return "\n".join(rows)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction"
    )
    parser.add_argument("input_json", help="Path to JSON file containing transactions")
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    vat_report = generate_vat_to_be_paid_from_json(args.input_json)
    print(_format_report(vat_report))
