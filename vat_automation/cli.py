"""CLI for generating VAT payable by jurisdiction."""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .vat import generate_vat_payable_by_jurisdiction


def _load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON input must be an array of transaction objects.")
        if not all(isinstance(item, dict) for item in data):
            raise ValueError("Each JSON transaction must be an object.")
        return data

    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            return [dict(row) for row in reader]

    raise ValueError("Unsupported input file type. Use .json or .csv.")


def _as_serializable(payable: dict[str, Decimal]) -> dict[str, str]:
    return {jurisdiction: format(amount, ".2f") for jurisdiction, amount in payable.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable totals for each jurisdiction."
    )
    parser.add_argument("input_file", help="Path to a .json or .csv transactions file.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    args = parser.parse_args()

    records = _load_records(Path(args.input_file))
    payable = generate_vat_payable_by_jurisdiction(records)
    output = _as_serializable(payable)

    if args.pretty:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(json.dumps(output, separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
