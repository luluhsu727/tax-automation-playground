"""Core VAT payable calculations grouped by jurisdiction.

The module intentionally supports multiple input shapes and helper names so it
can be reused by different exercises that ask for "VAT to be paid by
jurisdiction".
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

MONEY_PLACES = Decimal("0.01")
TWOPLACES = MONEY_PLACES
SALE = "sale"
PURCHASE = "purchase"
VALID_TRANSACTION_TYPES = {SALE, PURCHASE}

_SALE_ALIASES = {"sale", "sales", "output", "collected"}
_PURCHASE_ALIASES = {"purchase", "purchases", "input", "expense", "cost"}


class VatComputationError(ValueError):
    """Raised when transaction VAT data is invalid."""


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert an arbitrary value into Decimal with friendly errors."""
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive
        raise VatComputationError(
            f"Invalid decimal value for '{field_name}': {value!r}"
        ) from exc


def _to_money(amount: Decimal) -> Decimal:
    """Round to 2 decimal places using standard money rounding."""
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"false", "f", "0", "no", "n"}:
            return False
        if normalized in {"true", "t", "1", "yes", "y"}:
            return True
    return bool(value)


def _normalize_rate(vat_rate: Decimal) -> Decimal:
    if vat_rate < 0:
        raise VatComputationError("Transaction vat_rate cannot be negative.")
    if vat_rate > 1:
        if vat_rate > 100:
            raise VatComputationError("Transaction vat_rate cannot exceed 100%.")
        return vat_rate / Decimal("100")
    return vat_rate


def _normalize_transaction_type(value: Any, *, required: bool) -> str:
    raw = str(value).strip().lower()
    if not raw and not required:
        return SALE
    if raw in _SALE_ALIASES:
        return SALE
    if raw in _PURCHASE_ALIASES:
        return PURCHASE
    raise VatComputationError(
        f"Unsupported transaction_type '{value}'. Expected sale/output or purchase/input."
    )


def calculate_transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    """Calculate VAT value from either vat_amount or taxable+rate fields."""
    if "vat_amount" in transaction and transaction.get("vat_amount") not in (None, ""):
        vat_amount = _to_decimal(transaction["vat_amount"], field_name="vat_amount")
    else:
        taxable_key = "taxable_amount" if "taxable_amount" in transaction else "net_amount"
        rate_key = "vat_rate" if "vat_rate" in transaction else "tax_rate"
        if taxable_key not in transaction or rate_key not in transaction:
            raise VatComputationError(
                "Transaction must provide 'vat_amount' or both taxable/net amount and VAT rate."
            )
        taxable_amount = _to_decimal(transaction[taxable_key], field_name=taxable_key)
        vat_rate = _normalize_rate(_to_decimal(transaction[rate_key], field_name=rate_key))
        vat_amount = taxable_amount * vat_rate

    if vat_amount < 0:
        raise VatComputationError("VAT amount cannot be negative.")
    return _to_money(vat_amount)


class Transaction:
    """Flexible transaction model used by VAT calculation helpers."""

    def __init__(
        self,
        jurisdiction: str,
        transaction_type: str = SALE,
        vat_amount: Decimal | str | float | int | None = None,
        *,
        net_amount: Decimal | str | float | int | None = None,
        vat_rate: Decimal | str | float | int | None = None,
        taxable: bool = True,
    ) -> None:
        self.jurisdiction = str(jurisdiction).strip().upper()
        self.transaction_type = str(transaction_type).strip().lower() or SALE
        self.taxable = _to_bool(taxable)

        self.net_amount = (
            _to_decimal(net_amount, field_name="net_amount")
            if net_amount is not None
            else Decimal("0")
        )
        self.vat_rate = (
            _normalize_rate(_to_decimal(vat_rate, field_name="vat_rate"))
            if vat_rate is not None
            else Decimal("0")
        )

        if vat_amount is None and net_amount is not None and vat_rate is not None:
            computed = self.net_amount * self.vat_rate
        elif vat_amount is not None:
            computed = _to_decimal(vat_amount, field_name="vat_amount")
        else:
            raise VatComputationError(
                "Transaction requires vat_amount or both net_amount and vat_rate."
            )

        if computed < 0:
            raise VatComputationError("VAT amount cannot be negative.")
        self.vat_amount = _to_money(computed) if self.taxable else Decimal("0.00")

    def __repr__(self) -> str:  # pragma: no cover - debug representation
        return (
            "Transaction("
            f"jurisdiction={self.jurisdiction!r}, "
            f"transaction_type={self.transaction_type!r}, "
            f"vat_amount={self.vat_amount!r})"
        )


@dataclass(frozen=True)
class VATSummary:
    output_vat: Decimal
    input_vat: Decimal
    vat_payable: Decimal
    net_vat: Decimal
    vat_refundable: Decimal

    @property
    def vat_credit(self) -> Decimal:
        return self.vat_refundable


class VATPayableResult(dict[str, VATSummary]):
    """Dictionary-like result that also supports list-style comparison/indexing."""

    def __init__(self, summaries: Mapping[str, VATSummary]) -> None:
        ordered = dict(sorted(summaries.items()))
        super().__init__(ordered)
        self._rows = [
            {
                "jurisdiction": jurisdiction,
                "output_vat": summary.output_vat,
                "input_vat": summary.input_vat,
                "net_vat": summary.net_vat,
                "vat_payable": summary.vat_payable,
                "vat_refundable": summary.vat_refundable,
            }
            for jurisdiction, summary in ordered.items()
        ]

    def __getitem__(self, key: object) -> Any:
        if isinstance(key, int):
            return self._rows[key]
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, list):
            return self._rows == other
        return super().__eq__(other)


def transaction_from_record(record: Mapping[str, Any]) -> Transaction:
    """Create a Transaction from record formats commonly used in this repo."""
    jurisdiction = str(record.get("jurisdiction", record.get("country", ""))).strip()
    if not jurisdiction:
        raise VatComputationError("Record is missing a non-empty 'jurisdiction'.")

    transaction_type = _normalize_transaction_type(
        record.get("transaction_type", record.get("type", SALE)),
        required=True,
    )
    vat_amount = calculate_transaction_vat(record)
    taxable = _to_bool(record.get("taxable", True))

    return Transaction(
        jurisdiction=jurisdiction,
        transaction_type=transaction_type,
        vat_amount=vat_amount,
        taxable=taxable,
    )


def transaction_from_mapping(raw: Mapping[str, Any]) -> Transaction:
    """Build transaction from generic mapping payload."""
    try:
        jurisdiction = raw["jurisdiction"]
        transaction_type = raw["transaction_type"]
    except KeyError as exc:
        raise VatComputationError(f"Missing required field: {exc.args[0]}") from exc

    if "vat_amount" in raw and raw.get("vat_amount") not in (None, ""):
        return Transaction(
            jurisdiction=str(jurisdiction),
            transaction_type=str(transaction_type),
            vat_amount=raw["vat_amount"],
            taxable=_to_bool(raw.get("taxable", True)),
        )

    net_key = "net_amount" if "net_amount" in raw else "taxable_amount"
    rate_key = "vat_rate" if "vat_rate" in raw else "tax_rate"
    if net_key not in raw:
        raise VatComputationError("Missing required field: net_amount")
    if rate_key not in raw:
        raise VatComputationError("Missing required field: vat_rate")

    return Transaction(
        jurisdiction=str(jurisdiction),
        transaction_type=str(transaction_type),
        net_amount=raw[net_key],
        vat_rate=raw[rate_key],
        taxable=_to_bool(raw.get("taxable", True)),
    )


def load_transactions(path: str | Path) -> list[Transaction]:
    """Load JSON transactions from disk."""
    file_path = Path(path)
    records = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise VatComputationError("Input JSON must be an array of transaction records.")
    return [transaction_from_record(record) for record in records]


def _coerce_transaction(item: Transaction | Mapping[str, Any]) -> Transaction:
    if isinstance(item, Transaction):
        return item
    if isinstance(item, Mapping):
        return transaction_from_mapping(item)
    raise VatComputationError("Each transaction must be a Transaction or a mapping payload.")


def _validate_transaction(transaction: Transaction) -> None:
    if not transaction.jurisdiction:
        raise VatComputationError("Transaction jurisdiction must be non-empty.")
    if transaction.transaction_type not in VALID_TRANSACTION_TYPES:
        raise VatComputationError(
            f"Unsupported transaction_type '{transaction.transaction_type}'. "
            f"Expected one of {sorted(VALID_TRANSACTION_TYPES)}."
        )
    if transaction.vat_amount < 0:
        raise VatComputationError("VAT amount cannot be negative.")


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal]:
    """Return net VAT payable by jurisdiction."""
    totals: dict[str, Decimal] = {}
    for item in transactions:
        tx = _coerce_transaction(item)
        _validate_transaction(tx)

        current = totals.get(tx.jurisdiction, Decimal("0.00"))
        if tx.transaction_type == SALE:
            current += tx.vat_amount
        elif tx.transaction_type == PURCHASE:
            current -= tx.vat_amount
        totals[tx.jurisdiction] = current

    result: dict[str, Decimal] = {}
    for jurisdiction in sorted(totals):
        total = _to_money(totals[jurisdiction])
        if floor_at_zero and total < 0:
            total = Decimal("0.00")
        result[jurisdiction] = _to_money(total)
    return result


def calculate_vat_position_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Return VAT output/input/payable/credit per jurisdiction."""
    buckets: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for item in transactions:
        tx = _coerce_transaction(item)
        _validate_transaction(tx)
        if tx.transaction_type == SALE:
            buckets[tx.jurisdiction]["output_vat"] += tx.vat_amount
        else:
            buckets[tx.jurisdiction]["input_vat"] += tx.vat_amount

    positions: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _to_money(buckets[jurisdiction]["output_vat"])
        input_vat = _to_money(buckets[jurisdiction]["input_vat"])
        net = _to_money(output_vat - input_vat)
        vat_payable = net if net > 0 else Decimal("0.00")
        vat_credit = -net if net < 0 else Decimal("0.00")
        positions[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _to_money(vat_payable),
            "vat_credit": _to_money(vat_credit),
        }
    return positions


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
    *,
    jurisdiction_key: str = "jurisdiction",
    net_amount_key: str = "net_amount",
    vat_rate_key: str = "vat_rate",
    vat_amount_key: str = "vat_amount",
) -> dict[str, Decimal]:
    """Generate VAT payable amount by jurisdiction.

    Mapping payloads without transaction type are treated as output/sales VAT.
    The final "to be paid" value is floored to zero per jurisdiction.
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for item in transactions:
        if isinstance(item, Transaction):
            jurisdiction = item.jurisdiction
            tx_type = _normalize_transaction_type(item.transaction_type, required=True)
            amount = item.vat_amount
        elif isinstance(item, Mapping):
            jurisdiction = str(
                item.get(jurisdiction_key, item.get("jurisdiction", item.get("country", "")))
            ).strip()
            if not jurisdiction:
                raise VatComputationError("Missing required field: jurisdiction")

            proxy: dict[str, Any] = dict(item)
            if vat_amount_key in item and vat_amount_key != "vat_amount":
                proxy["vat_amount"] = item[vat_amount_key]
            if net_amount_key in item and net_amount_key not in {"net_amount", "taxable_amount"}:
                proxy["net_amount"] = item[net_amount_key]
            if vat_rate_key in item and vat_rate_key not in {"vat_rate", "tax_rate"}:
                proxy["vat_rate"] = item[vat_rate_key]

            amount = calculate_transaction_vat(proxy)
            tx_raw = item.get("transaction_type", item.get("type", SALE))
            tx_type = _normalize_transaction_type(tx_raw, required=False)
            jurisdiction = jurisdiction.upper()
        else:
            raise VatComputationError(
                "Each transaction must be a Transaction or mapping payload."
            )

        if tx_type == PURCHASE:
            totals[jurisdiction] -= amount
        else:
            totals[jurisdiction] += amount

    return {
        jurisdiction: (_to_money(total) if total > 0 else Decimal("0.00"))
        for jurisdiction, total in sorted(totals.items())
    }


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Compatibility alias for tasks phrased as 'for each jurisdiction'."""
    return generate_vat_to_be_paid_by_jurisdiction(transactions)


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> VATPayableResult:
    """Generate a detailed VAT summary by jurisdiction."""
    output_input: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for item in transactions:
        if isinstance(item, Transaction):
            jurisdiction = item.jurisdiction
            tx_type = _normalize_transaction_type(item.transaction_type, required=True)
            amount = item.vat_amount
        elif isinstance(item, Mapping):
            jurisdiction = str(item.get("jurisdiction", item.get("country", ""))).strip()
            if not jurisdiction:
                raise VatComputationError("Missing required field: jurisdiction")
            tx_type = _normalize_transaction_type(
                item.get("transaction_type", item.get("type", SALE)),
                required=True,
            )
            amount = calculate_transaction_vat(item)
            jurisdiction = jurisdiction.upper()
        else:
            raise VatComputationError(
                "Each transaction must be a Transaction or mapping payload."
            )

        if tx_type == SALE:
            output_input[jurisdiction]["output_vat"] += amount
        else:
            output_input[jurisdiction]["input_vat"] += amount

    summaries: dict[str, VATSummary] = {}
    for jurisdiction in sorted(output_input):
        output_vat = _to_money(output_input[jurisdiction]["output_vat"])
        input_vat = _to_money(output_input[jurisdiction]["input_vat"])
        net_vat = _to_money(output_vat - input_vat)
        vat_payable = net_vat if net_vat > 0 else Decimal("0.00")
        vat_refundable = -net_vat if net_vat < 0 else Decimal("0.00")
        summaries[jurisdiction] = VATSummary(
            output_vat=output_vat,
            input_vat=input_vat,
            vat_payable=_to_money(vat_payable),
            net_vat=net_vat,
            vat_refundable=_to_money(vat_refundable),
        )

    return VATPayableResult(summaries)


def _rate_to_fraction(value: Any) -> Decimal:
    rate = _to_decimal(value, field_name="vat_rate")
    return _normalize_rate(rate)


def _compute_output_vat(record: Mapping[str, Any]) -> Decimal:
    if "output_vat" in record and record.get("output_vat") not in (None, ""):
        return _to_decimal(record["output_vat"], field_name="output_vat")
    sales_amount = _to_decimal(record.get("sales_amount", 0), field_name="sales_amount")
    vat_rate = _rate_to_fraction(record.get("vat_rate", 0))
    return sales_amount * vat_rate


def _compute_input_vat(record: Mapping[str, Any]) -> Decimal:
    if "input_vat" in record and record.get("input_vat") not in (None, ""):
        return _to_decimal(record["input_vat"], field_name="input_vat")
    purchase_amount = _to_decimal(
        record.get("purchase_amount", 0), field_name="purchase_amount"
    )
    deductible_rate = _rate_to_fraction(record.get("deductible_vat_rate", 0))
    return purchase_amount * deductible_rate


def vat_payable_by_jurisdiction(records: list[dict[str, Any]]) -> dict[str, float]:
    """Alternative API: compute payable from output/input-style records."""
    output_totals: dict[str, Decimal] = {}
    input_totals: dict[str, Decimal] = {}

    for record in records:
        jurisdiction = record.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise VatComputationError(f"Invalid jurisdiction in record: {record!r}")

        output_vat = _compute_output_vat(record)
        input_vat = _compute_input_vat(record)
        output_totals[jurisdiction] = output_totals.get(jurisdiction, Decimal("0")) + output_vat
        input_totals[jurisdiction] = input_totals.get(jurisdiction, Decimal("0")) + input_vat

    results: dict[str, float] = {}
    for jurisdiction in sorted(set(output_totals) | set(input_totals)):
        payable = output_totals.get(jurisdiction, Decimal("0")) - input_totals.get(
            jurisdiction, Decimal("0")
        )
        payable = max(payable, Decimal("0"))
        results[jurisdiction] = float(_to_money(payable))
    return results


def _load_records(input_file: Path) -> list[dict[str, Any]]:
    payload = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise VatComputationError("Input JSON must be an array of records.")

    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            raise VatComputationError(f"Record at index {idx} must be an object.")
    return payload


def main() -> None:
    """Simple CLI for quick manual usage."""
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amount for each jurisdiction."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to input JSON file with jurisdiction VAT records.",
    )
    args = parser.parse_args()

    records = _load_records(args.input_file)
    result = vat_payable_by_jurisdiction(records)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = [
    "MONEY_PLACES",
    "PURCHASE",
    "SALE",
    "TWOPLACES",
    "VALID_TRANSACTION_TYPES",
    "VATPayableResult",
    "VATSummary",
    "Transaction",
    "VatComputationError",
    "calculate_transaction_vat",
    "calculate_vat_payable_by_jurisdiction",
    "calculate_vat_position_by_jurisdiction",
    "generate_vat_payable_by_jurisdiction",
    "generate_vat_to_be_paid_by_jurisdiction",
    "generate_vat_to_be_paid_for_each_jurisdiction",
    "load_transactions",
    "transaction_from_mapping",
    "transaction_from_record",
    "vat_payable_by_jurisdiction",
]
