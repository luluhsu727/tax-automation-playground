from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


TWOPLACES = Decimal("0.01")


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    net_amount: Decimal
    vat_rate: Decimal
    transaction_type: str
    vat_amount: Decimal | None = None


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Invalid decimal for '{field_name}': {value!r}") from exc


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _normalize_transaction(raw: dict) -> Transaction:
    required = {"jurisdiction", "net_amount", "vat_rate", "transaction_type"}
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError(f"Transaction missing required fields: {', '.join(sorted(missing))}")

    transaction_type = str(raw["transaction_type"]).strip().lower()
    if transaction_type not in {"sale", "purchase"}:
        raise ValueError(
            "transaction_type must be either 'sale' or 'purchase', "
            f"got {raw['transaction_type']!r}"
        )

    vat_amount = raw.get("vat_amount")
    return Transaction(
        jurisdiction=str(raw["jurisdiction"]).strip(),
        net_amount=_to_decimal(raw["net_amount"], "net_amount"),
        vat_rate=_to_decimal(raw["vat_rate"], "vat_rate"),
        transaction_type=transaction_type,
        vat_amount=_to_decimal(vat_amount, "vat_amount") if vat_amount is not None else None,
    )


def _transaction_vat_amount(transaction: Transaction) -> Decimal:
    if transaction.vat_amount is not None:
        return _quantize(transaction.vat_amount)
    return _quantize(transaction.net_amount * transaction.vat_rate)


def calculate_vat_payable_by_jurisdiction(
    raw_transactions: Iterable[dict],
) -> dict[str, dict[str, str]]:
    """
    Calculate VAT payable per jurisdiction.

    VAT payable = output VAT (sales) - input VAT (purchases)
    """
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for raw in raw_transactions:
        transaction = _normalize_transaction(raw)
        vat_amount = _transaction_vat_amount(transaction)

        if transaction.transaction_type == "sale":
            totals[transaction.jurisdiction]["output_vat"] += vat_amount
        else:
            totals[transaction.jurisdiction]["input_vat"] += vat_amount

    result: dict[str, dict[str, str]] = {}
    for jurisdiction, values in totals.items():
        output_vat = _quantize(values["output_vat"])
        input_vat = _quantize(values["input_vat"])
        payable = _quantize(output_vat - input_vat)
        result[jurisdiction] = {
            "output_vat": str(output_vat),
            "input_vat": str(input_vat),
            "vat_payable": str(payable),
        }
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute VAT payable per jurisdiction from a JSON transaction file."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input JSON file containing an array of transaction objects.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as input_file:
        transactions = json.load(input_file)

    result = calculate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
