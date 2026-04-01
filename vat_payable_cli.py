"""CLI for generating VAT payable by jurisdiction from JSON transactions."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from typing import Any, Dict, Iterable, Mapping

from vat_payable import calculate_vat_payable_by_jurisdiction


def _load_transactions(payload: Any) -> Iterable[Mapping[str, object]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "transactions" in payload and isinstance(
        payload["transactions"], list
    ):
        return payload["transactions"]
    raise ValueError(
        "Input JSON must be either a list of transactions or an object with a "
        "'transactions' list"
    )


def _serialize_decimals(values: Dict[str, Decimal]) -> Dict[str, str]:
    # Use string serialization to avoid floating-point rounding in output.
    return {jurisdiction: str(amount) for jurisdiction, amount in values.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable for each jurisdiction."
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Path to JSON input file (defaults to stdin).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args(argv)

    try:
        if args.input:
            with open(args.input, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        else:
            payload = json.load(sys.stdin)

        transactions = _load_transactions(payload)
        vat_payable = calculate_vat_payable_by_jurisdiction(transactions)
        output = {"vat_payable_by_jurisdiction": _serialize_decimals(vat_payable)}

        if args.pretty:
            json.dump(output, sys.stdout, indent=2, sort_keys=True)
            sys.stdout.write("\n")
        else:
            json.dump(output, sys.stdout, separators=(",", ":"), sort_keys=True)
            sys.stdout.write("\n")
        return 0
    except Exception as exc:  # pragma: no cover - simple CLI error path
        sys.stderr.write(f"Error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
