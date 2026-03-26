from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable, Mapping

MONEY_PRECISION = Decimal("0.01")
ZERO = Decimal("0.00")


def _to_decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal value: {value!r}") from exc


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def _parse_vat_rate(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.endswith("%"):
            return _to_decimal(candidate[:-1]) / Decimal("100")
        parsed = _to_decimal(candidate)
    else:
        parsed = _to_decimal(value)

    # Accept both decimal rates (0.20) and whole percentages (20).
    if parsed > Decimal("1"):
        return parsed / Decimal("100")
    return parsed


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    kind: str
    net_amount: Decimal
    vat_rate: Decimal
    vat_amount: Decimal | None = None

    @classmethod
    def from_mapping(cls, row: Mapping[str, object]) -> "Transaction":
        jurisdiction = str(row.get("jurisdiction", "")).strip()
        kind = str(row.get("kind", row.get("type", ""))).strip().lower()
        if not jurisdiction:
            raise ValueError("Missing required field: jurisdiction")
        if not kind:
            raise ValueError("Missing required field: kind/type")

        net_amount = _to_decimal(row.get("net_amount", "0"))
        vat_rate = _parse_vat_rate(row.get("vat_rate", "0"))

        vat_amount_raw = row.get("vat_amount")
        vat_amount = None
        if vat_amount_raw not in (None, ""):
            vat_amount = _to_decimal(vat_amount_raw)

        return cls(
            jurisdiction=jurisdiction,
            kind=kind,
            net_amount=net_amount,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
        )

    def resolved_vat_amount(self) -> Decimal:
        if self.vat_amount is not None:
            return _quantize_money(self.vat_amount)
        return _quantize_money(self.net_amount * self.vat_rate)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, object]],
) -> dict[str, dict[str, Decimal]]:
    totals: dict[str, dict[str, Decimal]] = {}

    for entry in transactions:
        tx = entry if isinstance(entry, Transaction) else Transaction.from_mapping(entry)
        vat_value = tx.resolved_vat_amount()
        bucket = totals.setdefault(
            tx.jurisdiction,
            {
                "output_vat": ZERO,
                "input_vat": ZERO,
            },
        )

        if tx.kind in {"sale", "sales", "output"}:
            bucket["output_vat"] += vat_value
        elif tx.kind in {"purchase", "purchases", "input"}:
            bucket["input_vat"] += vat_value
        else:
            raise ValueError(
                f"Unsupported kind {tx.kind!r} for jurisdiction {tx.jurisdiction!r}"
            )

    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction, values in sorted(totals.items()):
        output_vat = _quantize_money(values["output_vat"])
        input_vat = _quantize_money(values["input_vat"])
        net_vat = _quantize_money(output_vat - input_vat)
        vat_to_be_paid = net_vat if net_vat > ZERO else ZERO
        vat_credit = -net_vat if net_vat < ZERO else ZERO

        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "net_vat": net_vat,
            "vat_to_be_paid": _quantize_money(vat_to_be_paid),
            "vat_credit": _quantize_money(vat_credit),
        }

    return result


def load_transactions_from_csv(csv_path: Path) -> list[Transaction]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [Transaction.from_mapping(row) for row in reader]


def _serialize_for_json(payload: dict[str, dict[str, Decimal]]) -> dict[str, dict[str, str]]:
    return {
        jurisdiction: {key: f"{amount:.2f}" for key, amount in values.items()}
        for jurisdiction, values in payload.items()
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable by jurisdiction from transaction CSV."
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help=(
            "CSV with columns: jurisdiction, kind (sale|purchase), "
            "net_amount, vat_rate (or vat_amount)."
        ),
    )
    args = parser.parse_args()

    transactions = load_transactions_from_csv(args.csv_file)
    summary = generate_vat_payable_by_jurisdiction(transactions)
    print(json.dumps(_serialize_for_json(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
