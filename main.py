from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List

from vat_report import calculate_vat_by_jurisdiction, serialize_summary


def _load_transactions(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Input JSON must be an array of transactions.")
    return data


def run() -> None:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument(
        "input_json",
        help="Path to a JSON file containing an array of transaction records.",
    )
    args = parser.parse_args()

    transactions = _load_transactions(args.input_json)
    summary = calculate_vat_by_jurisdiction(transactions)
    print(json.dumps(serialize_summary(summary), indent=2))


if __name__ == "__main__":
    run()
