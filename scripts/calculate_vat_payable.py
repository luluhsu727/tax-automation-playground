#!/usr/bin/env python3
"""CLI to calculate VAT payable by jurisdiction from JSON transactions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

# Ensure local package imports resolve when running as a script path.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from vat import calculate_vat_payable_by_jurisdiction


def _load_transactions(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of transaction objects")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("Each transaction entry must be an object")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", type=Path, help="Path to transactions JSON file")
    args = parser.parse_args()

    transactions = _load_transactions(args.input_json)
    result = calculate_vat_payable_by_jurisdiction(transactions)
    output = {jurisdiction: summary.to_dict() for jurisdiction, summary in sorted(result.items())}
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
