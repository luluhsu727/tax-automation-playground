from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, Sequence


TWO_DP = Decimal("0.01")


def _to_decimal(value: object) -> Decimal:
    """Convert supported numeric inputs to Decimal."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    raise TypeError(f"Unsupported numeric value: {value!r}")


@dataclass(frozen=True)
class Transaction:
    """A VAT-relevant transaction row."""

    jurisdiction: str
    amount_ex_vat: Decimal
    vat_rate: Decimal
    transaction_type: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "Transaction":
        return cls(
            jurisdiction=str(data["jurisdiction"]),
            amount_ex_vat=_to_decimal(data["amount_ex_vat"]),
            vat_rate=_to_decimal(data["vat_rate"]),
            transaction_type=str(data["transaction_type"]).strip().lower(),
        )

    def vat_amount(self) -> Decimal:
        return (self.amount_ex_vat * self.vat_rate).quantize(TWO_DP, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, Decimal]:
    """Generate net VAT payable for each jurisdiction.

    Positive values indicate VAT payable to tax authorities.
    Negative values indicate a reclaim/credit position.
    """

    totals: dict[str, Decimal] = {}
    for raw_transaction in transactions:
        transaction = (
            raw_transaction
            if isinstance(raw_transaction, Transaction)
            else Transaction.from_mapping(raw_transaction)
        )

        jurisdiction = transaction.jurisdiction.strip()
        if not jurisdiction:
            raise ValueError("Jurisdiction must be non-empty")
        if transaction.vat_rate < 0:
            raise ValueError("VAT rate cannot be negative")

        vat = transaction.vat_amount()
        if transaction.transaction_type == "sale":
            delta = vat
        elif transaction.transaction_type == "purchase":
            delta = -vat
        else:
            raise ValueError(
                f"Unsupported transaction_type {transaction.transaction_type!r}; "
                "use 'sale' or 'purchase'"
            )

        totals[jurisdiction] = (totals.get(jurisdiction, Decimal("0")) + delta).quantize(
            TWO_DP, rounding=ROUND_HALF_UP
        )

    return dict(sorted(totals.items(), key=lambda item: item[0]))


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, Decimal]:
    """Compatibility alias for alternate naming."""
    return generate_vat_payable_by_jurisdiction(transactions)


def _parse_transactions_file(path: str) -> Sequence[Mapping[str, object]]:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transactions")
    return payload


def _json_ready_totals(totals: Mapping[str, Decimal]) -> dict[str, str]:
    return {key: format(value.quantize(TWO_DP, rounding=ROUND_HALF_UP), "f") for key, value in totals.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate VAT payable by jurisdiction")
    parser.add_argument(
        "transactions_json",
        help="Path to JSON file containing a list of transactions",
    )
    args = parser.parse_args()

    transactions = _parse_transactions_file(args.transactions_json)
    totals = generate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(_json_ready_totals(totals), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
