"""CLI entrypoint for VAT payable calculations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .calculator import calculate_vat_payable_by_jurisdiction, serialize_totals


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate VAT payable for each jurisdiction from transactions."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to a JSON file containing a list of transaction objects.",
    )
    return parser


def _load_transactions(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as file_handle:
            payload = json.load(file_handle)
    except FileNotFoundError as exc:
        raise ValueError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in input file: {path}") from exc

    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transactions")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("Every transaction must be a JSON object")

    return payload


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        transactions = _load_transactions(args.input_file)
        totals = calculate_vat_payable_by_jurisdiction(transactions)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    print(json.dumps(serialize_totals(totals), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
