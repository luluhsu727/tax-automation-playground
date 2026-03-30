#!/usr/bin/env python3
"""
Compute VAT payable totals per jurisdiction.

Expected input:
- JSON array of transaction objects, or
- JSON object with a top-level "transactions" array.

Each transaction supports:
- jurisdiction (str): jurisdiction key
- amount (number): taxable amount
- vat_rate (number): VAT rate as decimal (0.2) or percent (20)
- vat_collected (number, optional): output VAT already collected for this txn
- vat_paid (number, optional): input VAT already paid for this txn

Rules:
- If vat_collected is missing, it is computed as amount * normalized(vat_rate).
- If vat_paid is missing, it defaults to 0.
- payable = max(sum(vat_collected) - sum(vat_paid), 0) per jurisdiction.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Iterable, List, Mapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: object, field: str) -> Decimal:
    """Convert arbitrary numeric-like value into Decimal safely."""
    if value is None:
        raise ValueError(f"Missing required field: {field}")
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc


def _normalize_rate(rate: Decimal) -> Decimal:
    """Accept either decimal form (0.2) or percent form (20)."""
    if rate < 0:
        raise ValueError("vat_rate cannot be negative")
    if rate > 1:
        return rate / Decimal("100")
    return rate


@dataclass(frozen=True)
class JurisdictionTotals:
    output_vat: Decimal
    input_vat: Decimal

    @property
    def vat_payable(self) -> Decimal:
        return max(self.output_vat - self.input_vat, Decimal("0"))


def compute_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
) -> Dict[str, Dict[str, str]]:
    """
    Aggregate VAT payable by jurisdiction.

    Returns mapping:
      jurisdiction -> {
        "output_vat": "x.xx",
        "input_vat": "x.xx",
        "vat_payable": "x.xx"
      }
    """
    aggregates: Dict[str, JurisdictionTotals] = {}

    for idx, txn in enumerate(transactions):
        jurisdiction = txn.get("jurisdiction")
        if not isinstance(jurisdiction, str) or not jurisdiction.strip():
            raise ValueError(f"Transaction at index {idx} has invalid jurisdiction")

        amount = _to_decimal(txn.get("amount"), "amount")
        if amount < 0:
            raise ValueError(f"Transaction at index {idx} has negative amount")

        vat_collected_raw = txn.get("vat_collected")
        if vat_collected_raw is None:
            rate = _normalize_rate(_to_decimal(txn.get("vat_rate"), "vat_rate"))
            output_vat = amount * rate
        else:
            output_vat = _to_decimal(vat_collected_raw, "vat_collected")

        vat_paid_raw = txn.get("vat_paid")
        input_vat = (
            Decimal("0")
            if vat_paid_raw is None
            else _to_decimal(vat_paid_raw, "vat_paid")
        )

        if output_vat < 0 or input_vat < 0:
            raise ValueError(f"Transaction at index {idx} has negative VAT values")

        current = aggregates.get(
            jurisdiction, JurisdictionTotals(output_vat=Decimal("0"), input_vat=Decimal("0"))
        )
        aggregates[jurisdiction] = JurisdictionTotals(
            output_vat=current.output_vat + output_vat,
            input_vat=current.input_vat + input_vat,
        )

    def _fmt(value: Decimal) -> str:
        return str(value.quantize(TWOPLACES, rounding=ROUND_HALF_UP))

    result: Dict[str, Dict[str, str]] = {}
    for jurisdiction in sorted(aggregates):
        totals = aggregates[jurisdiction]
        result[jurisdiction] = {
            "output_vat": _fmt(totals.output_vat),
            "input_vat": _fmt(totals.input_vat),
            "vat_payable": _fmt(totals.vat_payable),
        }

    return result


def _extract_transactions(payload: object) -> List[Mapping[str, object]]:
    if isinstance(payload, list):
        transactions = payload
    elif isinstance(payload, dict) and isinstance(payload.get("transactions"), list):
        transactions = payload["transactions"]
    else:
        raise ValueError(
            "Input JSON must be an array of transactions or an object with a "
            '"transactions" array'
        )

    normalized: List[Mapping[str, object]] = []
    for idx, item in enumerate(transactions):
        if not isinstance(item, dict):
            raise ValueError(f"Transaction at index {idx} must be an object")
        normalized.append(item)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable per jurisdiction from a JSON file.",
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to JSON input containing transactions",
    )
    args = parser.parse_args()

    payload = json.loads(args.input_file.read_text(encoding="utf-8"))
    transactions = _extract_transactions(payload)
    result = compute_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
