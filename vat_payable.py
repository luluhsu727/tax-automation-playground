"""VAT payable calculation utilities.

This module provides a reusable function to compute VAT payable
for each jurisdiction from a list of transactions.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Mapping


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class JurisdictionVatSummary:
    """Aggregated VAT numbers for a single jurisdiction."""

    output_vat: Decimal = Decimal("0")
    input_vat: Decimal = Decimal("0")

    @property
    def vat_payable(self) -> Decimal:
        return self.output_vat - self.input_vat

    def to_dict(self) -> Dict[str, float]:
        return {
            "output_vat": float(_round_money(self.output_vat)),
            "input_vat": float(_round_money(self.input_vat)),
            "vat_payable": float(_round_money(self.vat_payable)),
        }


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive conversion guard
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _round_money(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _resolve_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        return _to_decimal(transaction["vat_amount"], "vat_amount")

    amount = transaction.get("amount")
    rate = transaction.get("vat_rate")
    if amount is None or rate is None:
        raise ValueError(
            "Each transaction must include either 'vat_amount' "
            "or both 'amount' and 'vat_rate'."
        )

    return _to_decimal(amount, "amount") * _to_decimal(rate, "vat_rate")


def _resolve_flow(transaction_type: str) -> str:
    normalized = transaction_type.strip().lower()
    if normalized in {"sale", "sales", "output", "output_vat"}:
        return "output"
    if normalized in {"purchase", "purchases", "input", "input_vat", "expense"}:
        return "input"

    raise ValueError(
        "Unsupported transaction type. Expected one of "
        "{sale/output/purchase/input} aliases."
    )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """Return output VAT, input VAT, and VAT payable per jurisdiction.

    Parameters
    ----------
    transactions:
        Iterable of transaction mappings.
        Required fields per transaction:
          - jurisdiction (str)
          - type (sale/output or purchase/input aliases)
          - either vat_amount, or both amount and vat_rate

    Returns
    -------
    dict
        {
          "<jurisdiction>": {
            "output_vat": ...,
            "input_vat": ...,
            "vat_payable": ...
          },
          ...
        }
    """

    ledger: Dict[str, Dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for idx, transaction in enumerate(transactions):
        if not isinstance(transaction, Mapping):
            raise ValueError(f"Transaction at index {idx} must be a mapping.")

        jurisdiction = transaction.get("jurisdiction")
        tx_type = transaction.get("type")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise ValueError(
                f"Transaction at index {idx} must include a non-empty 'jurisdiction'."
            )
        if not tx_type or not isinstance(tx_type, str):
            raise ValueError(
                f"Transaction at index {idx} must include a non-empty string 'type'."
            )

        vat_amount = _resolve_vat_amount(transaction)
        flow = _resolve_flow(tx_type)

        if flow == "output":
            ledger[jurisdiction]["output_vat"] += vat_amount
        else:
            ledger[jurisdiction]["input_vat"] += vat_amount

    response: Dict[str, Dict[str, float]] = {}
    for jurisdiction in sorted(ledger):
        summary = JurisdictionVatSummary(
            output_vat=ledger[jurisdiction]["output_vat"],
            input_vat=ledger[jurisdiction]["input_vat"],
        )
        response[jurisdiction] = summary.to_dict()
    return response


def _load_transactions(path: str) -> List[Mapping[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "transactions" in payload and isinstance(
        payload["transactions"], list
    ):
        return payload["transactions"]

    raise ValueError(
        "JSON input must be either a list of transactions "
        "or an object with a 'transactions' list."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable per jurisdiction from JSON transactions."
    )
    parser.add_argument(
        "input_file",
        help="Path to a JSON file with transactions.",
    )
    args = parser.parse_args()

    transactions = _load_transactions(args.input_file)
    result = calculate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
