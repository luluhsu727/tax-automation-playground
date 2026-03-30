from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Mapping


TWOPLACES = Decimal("0.01")

SIGN_BY_TRANSACTION_TYPE = {
    "sale": Decimal("1"),
    "refund": Decimal("-1"),
    "purchase": Decimal("-1"),
    "purchase_refund": Decimal("1"),
}


def _to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
    default_vat_rates: Mapping[str, Any] | None = None,
) -> Dict[str, Decimal]:
    """
    Aggregate VAT payable by jurisdiction.

    Transaction fields:
      - jurisdiction (required)
      - net_amount (required unless vat_amount is present)
      - vat_rate (optional if default_vat_rates provides one)
      - vat_amount (optional explicit VAT amount; overrides computed VAT)
      - transaction_type (optional): sale, refund, purchase, purchase_refund
    """
    default_vat_rates = default_vat_rates or {}
    vat_payable: Dict[str, Decimal] = {}

    for idx, transaction in enumerate(transactions):
        jurisdiction = transaction.get("jurisdiction")
        if not jurisdiction:
            raise ValueError(f"Transaction at index {idx} is missing 'jurisdiction'")

        transaction_type = transaction.get("transaction_type", "sale")
        sign = SIGN_BY_TRANSACTION_TYPE.get(transaction_type)
        if sign is None:
            valid = ", ".join(sorted(SIGN_BY_TRANSACTION_TYPE))
            raise ValueError(
                f"Transaction at index {idx} has invalid 'transaction_type' "
                f"'{transaction_type}'. Expected one of: {valid}"
            )

        if "vat_amount" in transaction and transaction["vat_amount"] is not None:
            vat_amount = _to_decimal(transaction["vat_amount"])
        else:
            if "net_amount" not in transaction or transaction["net_amount"] is None:
                raise ValueError(
                    f"Transaction at index {idx} must include 'net_amount' "
                    "when 'vat_amount' is not provided"
                )
            net_amount = _to_decimal(transaction["net_amount"])

            vat_rate = transaction.get("vat_rate")
            if vat_rate is None:
                vat_rate = default_vat_rates.get(jurisdiction)
            if vat_rate is None:
                raise ValueError(
                    f"Transaction at index {idx} missing VAT rate for jurisdiction "
                    f"'{jurisdiction}'. Provide 'vat_rate' or default_vat_rates."
                )

            vat_amount = net_amount * _to_decimal(vat_rate)

        vat_payable[jurisdiction] = vat_payable.get(jurisdiction, Decimal("0")) + (
            sign * vat_amount
        )

    return {k: _quantize(v) for k, v in sorted(vat_payable.items())}


def _stringify_decimals(values: Mapping[str, Decimal]) -> Dict[str, str]:
    return {key: f"{value:.2f}" for key, value in values.items()}


def build_cli_output(payload: Mapping[str, Any]) -> Dict[str, Any]:
    default_vat_rates = payload.get("default_vat_rates", {})
    transactions = payload.get("transactions", [])

    vat_by_jurisdiction = generate_vat_payable_by_jurisdiction(
        transactions=transactions,
        default_vat_rates=default_vat_rates,
    )
    total = _quantize(sum(vat_by_jurisdiction.values(), Decimal("0")))

    return {
        "vat_payable_by_jurisdiction": _stringify_decimals(vat_by_jurisdiction),
        "total_vat_payable": f"{total:.2f}",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to JSON input file with transactions and VAT rates",
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as file:
        payload = json.load(file)

    output = build_cli_output(payload)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
