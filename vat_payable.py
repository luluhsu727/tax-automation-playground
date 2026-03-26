from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping


TWOPLACES = Decimal("0.01")


def _to_decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Unable to parse decimal value: {value}") from exc


def _transaction_vat_amount(transaction: Mapping[str, object]) -> Decimal:
    if transaction.get("vat_amount") is not None and transaction.get("vat_amount") != "":
        return _to_decimal(transaction["vat_amount"])

    net_amount = transaction.get("net_amount")
    vat_rate = transaction.get("vat_rate")
    if net_amount is None or vat_rate is None or net_amount == "" or vat_rate == "":
        raise ValueError(
            "Each transaction must provide vat_amount or both net_amount and vat_rate."
        )
    return _to_decimal(net_amount) * _to_decimal(vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, object]],
    places: Decimal = TWOPLACES,
) -> Dict[str, Dict[str, Decimal]]:
    """
    Aggregate VAT payable for each jurisdiction.

    Rules:
    - sale transactions increase output VAT (tax collected)
    - purchase transactions increase input VAT (recoverable tax)
    - VAT payable = output VAT - input VAT
    """
    totals: MutableMapping[str, MutableMapping[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0"), "input_vat": Decimal("0")}
    )

    for tx in transactions:
        jurisdiction = str(tx.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Transaction is missing jurisdiction.")

        tx_type = str(tx.get("transaction_type", "")).strip().lower()
        if tx_type not in {"sale", "purchase"}:
            raise ValueError(
                f"Unsupported transaction_type '{tx_type}'. Use 'sale' or 'purchase'."
            )

        vat_amount = _transaction_vat_amount(tx)
        if tx_type == "sale":
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    result: Dict[str, Dict[str, Decimal]] = {}
    for jurisdiction, amounts in sorted(totals.items()):
        output_vat = amounts["output_vat"].quantize(places, rounding=ROUND_HALF_UP)
        input_vat = amounts["input_vat"].quantize(places, rounding=ROUND_HALF_UP)
        vat_payable = (output_vat - input_vat).quantize(places, rounding=ROUND_HALF_UP)
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": vat_payable,
        }
    return result


def load_transactions_from_csv(path: str | Path) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _decimal_to_string(payload: Mapping[str, Mapping[str, Decimal]]) -> Dict[str, Dict[str, str]]:
    return {
        jurisdiction: {field: f"{value:.2f}" for field, value in values.items()}
        for jurisdiction, values in payload.items()
    }


def _build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from a CSV file."
    )
    parser.add_argument("csv_path", help="Input CSV file path.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as JSON (default output is a fixed-width table).",
    )
    return parser


def main() -> None:
    parser = _build_cli()
    args = parser.parse_args()

    transactions = load_transactions_from_csv(args.csv_path)
    result = generate_vat_payable_by_jurisdiction(transactions)
    printable = _decimal_to_string(result)

    if args.json:
        print(json.dumps(printable, indent=2, sort_keys=True))
        return

    header = f"{'Jurisdiction':<16} {'Output VAT':>12} {'Input VAT':>12} {'VAT Payable':>12}"
    print(header)
    print("-" * len(header))
    for jurisdiction, values in printable.items():
        print(
            f"{jurisdiction:<16} "
            f"{values['output_vat']:>12} "
            f"{values['input_vat']:>12} "
            f"{values['vat_payable']:>12}"
        )


if __name__ == "__main__":
    main()
