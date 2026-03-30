"""Core VAT payable calculations grouped by jurisdiction.

This module intentionally supports multiple helper names and input shapes used
across VAT automation exercises.
"""

from __future__ import annotations

import argparse
import csv
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

_SALE_ALIASES = {"sale", "sales", "output", "collected", "invoice"}
_PURCHASE_ALIASES = {"purchase", "purchases", "input", "expense", "cost", "bill"}
CSV_VAT_RATES = {
    "DE": Decimal("0.19"),
    "FR": Decimal("0.20"),
    "ES": Decimal("0.21"),
    "IT": Decimal("0.22"),
}


class VatComputationError(ValueError):
    """Raised when transaction VAT data is invalid."""


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    """Convert an arbitrary value into Decimal with clear errors."""
    try:
        text = str(value).strip()
        if text.endswith("%"):
            text = text[:-1].strip()
        return Decimal(text)
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
    raw = str(value or "").strip().lower()
    if not raw and not required:
        return SALE
    if raw in _SALE_ALIASES:
        return SALE
    if raw in _PURCHASE_ALIASES:
        return PURCHASE
    raise VatComputationError(
        f"Unsupported transaction_type '{value}'. Expected sale/output or purchase/input."
    )


def _extract_transaction_type(transaction: Mapping[str, Any], *, required: bool) -> str:
    if "tax_direction" in transaction and transaction.get("tax_direction") not in (None, ""):
        return _normalize_transaction_type(transaction.get("tax_direction"), required=True)
    return _normalize_transaction_type(
        transaction.get("transaction_type", transaction.get("type", transaction.get("kind", ""))),
        required=required,
    )


def calculate_transaction_vat(transaction: Mapping[str, Any]) -> Decimal:
    """Calculate VAT value from either vat_amount or taxable+rate fields."""
    if "vat_amount" in transaction and transaction.get("vat_amount") not in (None, ""):
        vat_amount = _to_decimal(transaction["vat_amount"], field_name="vat_amount")
    else:
        taxable_key = "taxable_amount" if "taxable_amount" in transaction else None
        if taxable_key is None and "net_amount" in transaction:
            taxable_key = "net_amount"
        if taxable_key is None and "amount_ex_vat" in transaction:
            taxable_key = "amount_ex_vat"
        if taxable_key is None and "amount" in transaction:
            taxable_key = "amount"

        rate_key = "vat_rate" if "vat_rate" in transaction else None
        if rate_key is None and "tax_rate" in transaction:
            rate_key = "tax_rate"

        if taxable_key is None or rate_key is None:
            raise VatComputationError(
                "Transaction must provide 'vat_amount' or both taxable/net amount and VAT rate."
            )

        taxable_amount = _to_decimal(transaction[taxable_key], field_name=taxable_key)
        vat_rate = _normalize_rate(_to_decimal(transaction[rate_key], field_name=rate_key))
        vat_amount = taxable_amount * vat_rate

    if vat_amount < 0:
        raise VatComputationError("VAT amount cannot be negative.")
    return _to_money(vat_amount)


def _build_structured_result(
    net_totals: Mapping[str, Decimal],
) -> VATPayableResult:
    summaries: dict[str, VATSummary] = {}
    for jurisdiction in sorted(net_totals):
        net_vat = _to_money(net_totals[jurisdiction])
        if net_vat >= 0:
            output_vat = net_vat
            input_vat = Decimal("0.00")
        else:
            output_vat = Decimal("0.00")
            input_vat = -net_vat

        vat_payable = net_vat if net_vat > 0 else Decimal("0.00")
        vat_refundable = -net_vat if net_vat < 0 else Decimal("0.00")
        summaries[jurisdiction] = VATSummary(
            output_vat=_to_money(output_vat),
            input_vat=_to_money(input_vat),
            net_vat=net_vat,
            vat_payable=_to_money(vat_payable),
            vat_refundable=_to_money(vat_refundable),
        )
    return VATPayableResult(summaries)


def _looks_like_amount_ex_vat_payload(
    transactions: list[Transaction | Mapping[str, Any]],
) -> bool:
    if not transactions:
        return False
    has_transaction_object = any(isinstance(item, Transaction) for item in transactions)
    if has_transaction_object:
        return True
    for item in transactions:
        if not isinstance(item, Mapping):
            return False
        if (
            "amount_ex_vat" not in item
            and "net_amount" not in item
            and "amount" not in item
            and "taxable_amount" not in item
        ):
            return False
    return True


class Transaction:
    """Flexible transaction model used by VAT calculation helpers."""

    def __init__(
        self,
        jurisdiction: str,
        transaction_type: str = SALE,
        vat_amount: Decimal | str | float | int | None = None,
        *,
        net_amount: Decimal | str | float | int | None = None,
        amount_ex_vat: Decimal | str | float | int | None = None,
        amount: Decimal | str | float | int | None = None,
        vat_rate: Decimal | str | float | int | None = None,
        taxable: bool = True,
    ) -> None:
        self.jurisdiction = str(jurisdiction).strip().upper()
        self.transaction_type = _normalize_transaction_type(transaction_type, required=True)
        self.taxable = _to_bool(taxable)

        if net_amount is None and amount_ex_vat is not None:
            net_amount = amount_ex_vat
        if net_amount is None and amount is not None:
            net_amount = amount

        self.net_amount = (
            _to_decimal(net_amount, field_name="net_amount")
            if net_amount is not None
            else Decimal("0")
        )
        self.amount_ex_vat = self.net_amount
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


class VATTransaction(Transaction):
    """Compatibility transaction shape with amount and vat_rate fields."""

    def __init__(
        self,
        jurisdiction: str,
        amount: Decimal | str | float | int,
        vat_rate: Decimal | str | float | int,
        transaction_type: str = SALE,
        vat_amount: Decimal | str | float | int | None = None,
        *,
        taxable: bool = True,
    ) -> None:
        self.amount = _to_decimal(amount, field_name="amount")
        super().__init__(
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            vat_amount=vat_amount,
            net_amount=self.amount,
            vat_rate=vat_rate,
            taxable=taxable,
        )


class VATSummary(dict[str, Decimal]):
    """A dict-like summary with property access for common VAT fields."""

    def __init__(
        self,
        *,
        output_vat: Decimal,
        input_vat: Decimal,
        net_vat: Decimal,
        vat_payable: Decimal,
        vat_refundable: Decimal,
    ) -> None:
        payable_value = _to_money(vat_payable)
        refundable_value = _to_money(vat_refundable)
        super().__init__(
            output_vat=_to_money(output_vat),
            input_vat=_to_money(input_vat),
            net_vat=_to_money(net_vat),
            vat_payable=payable_value,
            vat_refundable=refundable_value,
            vat_to_be_paid=payable_value,
            vat_credit=refundable_value,
        )

    def __getitem__(self, key: str) -> Decimal:
        if key == "vat_to_be_paid":
            key = "vat_payable"
        elif key == "vat_credit":
            key = "vat_refundable"
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Decimal):
            return self.vat_payable == other
        if isinstance(other, Mapping):
            for key, value in other.items():
                if self[key] != value:
                    return False
            return True
        return super().__eq__(other)

    @property
    def output_vat(self) -> Decimal:
        return self["output_vat"]

    @property
    def input_vat(self) -> Decimal:
        return self["input_vat"]

    @property
    def net_vat(self) -> Decimal:
        return self["net_vat"]

    @property
    def vat_payable(self) -> Decimal:
        return self["vat_payable"]

    @property
    def vat_refundable(self) -> Decimal:
        return self["vat_refundable"]

    @property
    def vat_credit(self) -> Decimal:
        return self["vat_refundable"]

    @property
    def vat_to_be_paid(self) -> Decimal:
        return self["vat_payable"]


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
                "vat_to_be_paid": summary.vat_to_be_paid,
                "vat_credit": summary.vat_credit,
            }
            for jurisdiction, summary in ordered.items()
        ]

    def __getitem__(self, key: object) -> Any:
        if isinstance(key, int):
            return self._rows[key]
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, list):
            if len(self._rows) != len(other):
                return False
            for row, expected in zip(self._rows, other):
                if not isinstance(expected, Mapping):
                    return False
                for key, value in expected.items():
                    if row.get(key) != value:
                        return False
            return True
        return super().__eq__(other)


@dataclass(frozen=True)
class CalculateVatSummary:
    """Summary row used by tax-direction style calculations."""

    jurisdiction: str
    output_vat: Decimal
    input_vat: Decimal
    net_vat: Decimal
    vat_to_be_paid: Decimal
    vat_credit: Decimal


def transaction_from_record(record: Mapping[str, Any]) -> Transaction:
    """Create a Transaction from record formats commonly used in this repo."""
    jurisdiction = str(record.get("jurisdiction", record.get("country", ""))).strip()
    if not jurisdiction:
        raise VatComputationError("Record is missing a non-empty 'jurisdiction'.")

    transaction_type = _extract_transaction_type(record, required=False)
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
    return transaction_from_record(raw)


def _clean_csv_row(row: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, str):
            stripped = value.strip()
            cleaned[key] = None if stripped == "" else stripped
        else:
            cleaned[key] = value
    return cleaned


def read_transactions_from_csv(csv_path: str | Path) -> list[dict[str, Any]]:
    """Read CSV transactions into mapping rows, keeping original columns."""
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [_clean_csv_row(row) for row in reader]


def load_transactions(path: str | Path) -> list[Transaction]:
    """Load transactions from JSON or CSV path."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        rows = read_transactions_from_csv(file_path)
        return [transaction_from_record(row) for row in rows]

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


def _calculate_with_default_rates(
    transactions: Iterable[Transaction | Mapping[str, Any]],
    vat_rates_by_jurisdiction: Mapping[str, Any],
) -> dict[str, dict[str, Decimal]]:
    rates = {
        str(jurisdiction).upper(): _normalize_rate(
            _to_decimal(rate, field_name=f"vat rate for {jurisdiction}")
        )
        for jurisdiction, rate in vat_rates_by_jurisdiction.items()
    }

    report: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "taxable_sales": Decimal("0"),
            "taxable_purchases": Decimal("0"),
            "output_vat": Decimal("0"),
            "input_vat": Decimal("0"),
        }
    )

    for item in transactions:
        if isinstance(item, Transaction):
            jurisdiction = item.jurisdiction
            tx_type = item.transaction_type
            vat_value = item.vat_amount
            base_amount = item.net_amount
        elif isinstance(item, Mapping):
            jurisdiction = str(item.get("jurisdiction", item.get("country", ""))).strip().upper()
            if not jurisdiction:
                raise VatComputationError(f"Transaction missing jurisdiction: {item!r}")

            tx_type = _extract_transaction_type(item, required=True)
            if "vat_amount" in item and item.get("vat_amount") not in (None, ""):
                vat_value = _to_decimal(item["vat_amount"], field_name="vat_amount")
                base_amount = _to_decimal(item.get("amount", item.get("net_amount", 0)), field_name="amount")
            else:
                amount_key = "amount" if "amount" in item else "net_amount"
                if amount_key not in item and "taxable_amount" in item:
                    amount_key = "taxable_amount"
                if amount_key not in item:
                    raise VatComputationError(f"Invalid amount: {item.get('amount')!r}")
                base_amount = _to_decimal(item.get(amount_key), field_name=amount_key)
                tx_rate_raw = item.get("vat_rate")
                if tx_rate_raw is None:
                    if jurisdiction not in rates:
                        raise VatComputationError(
                            f"No default VAT rate configured for jurisdiction {jurisdiction!r}"
                        )
                    rate = rates[jurisdiction]
                else:
                    rate = _normalize_rate(_to_decimal(tx_rate_raw, field_name="vat_rate"))
                vat_value = base_amount * rate
        else:
            raise VatComputationError("Each transaction must be a Transaction or a mapping payload.")

        vat_value = _to_money(vat_value)
        bucket = report[jurisdiction]
        if tx_type == SALE:
            bucket["taxable_sales"] += base_amount
            bucket["output_vat"] += vat_value
        else:
            bucket["taxable_purchases"] += base_amount
            bucket["input_vat"] += vat_value

    finalized: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(report):
        totals = report[jurisdiction]
        output_vat = _to_money(totals["output_vat"])
        input_vat = _to_money(totals["input_vat"])
        finalized[jurisdiction] = {
            "taxable_sales": _to_money(totals["taxable_sales"]),
            "taxable_purchases": _to_money(totals["taxable_purchases"]),
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _to_money(output_vat - input_vat),
        }
    return finalized


def _normalize_tax_direction(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in _SALE_ALIASES:
        return SALE
    if raw in _PURCHASE_ALIASES:
        return PURCHASE
    raise VatComputationError(
        f"Unsupported tax_direction value {value!r}. "
        "Use one of output/sale/sales/collected/input/purchase/purchases."
    )


def _looks_like_tax_direction_rows(
    transactions: list[Transaction | Mapping[str, Any]],
) -> bool:
    if not transactions:
        return False
    any_mapping = False
    for item in transactions:
        if isinstance(item, Mapping):
            any_mapping = True
            if "tax_direction" not in item:
                return False
        else:
            return False
    return any_mapping


def _calculate_from_tax_direction_rows(
    transactions: list[Mapping[str, Any]],
) -> list[CalculateVatSummary]:
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for row in transactions:
        jurisdiction = str(row.get("jurisdiction", "")).strip().upper()
        if not jurisdiction:
            raise VatComputationError("Row is missing required field 'jurisdiction'.")
        direction = _normalize_tax_direction(row.get("tax_direction"))
        vat_amount = _to_money(_to_decimal(row.get("vat_amount"), field_name="vat_amount"))

        if direction == SALE:
            totals[jurisdiction]["output_vat"] += vat_amount
        else:
            totals[jurisdiction]["input_vat"] += vat_amount

    result: list[CalculateVatSummary] = []
    for jurisdiction in sorted(totals):
        output_vat = _to_money(totals[jurisdiction]["output_vat"])
        input_vat = _to_money(totals[jurisdiction]["input_vat"])
        net_vat = _to_money(output_vat - input_vat)
        vat_to_be_paid = net_vat if net_vat > 0 else Decimal("0.00")
        vat_credit = -net_vat if net_vat < 0 else Decimal("0.00")
        result.append(
            CalculateVatSummary(
                jurisdiction=jurisdiction,
                output_vat=output_vat,
                input_vat=input_vat,
                net_vat=net_vat,
                vat_to_be_paid=_to_money(vat_to_be_paid),
                vat_credit=_to_money(vat_credit),
            )
        )
    return result


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
    vat_rates_by_jurisdiction: Mapping[str, Any] | None = None,
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal] | dict[str, dict[str, Decimal]] | list[CalculateVatSummary]:
    """Return VAT payable by jurisdiction.

    - With ``vat_rates_by_jurisdiction`` provided, returns a detailed report with
      output/input VAT and taxable totals.
    - Otherwise returns net payable totals per jurisdiction.
    """
    tx_list = list(transactions)

    if vat_rates_by_jurisdiction is not None:
        return _calculate_with_default_rates(tx_list, vat_rates_by_jurisdiction)

    if _looks_like_tax_direction_rows(tx_list):
        return _calculate_from_tax_direction_rows(
            [row for row in tx_list if isinstance(row, Mapping)]
        )

    totals: dict[str, Decimal] = {}
    for item in tx_list:
        if isinstance(item, Mapping) and (
            "vat_collected" in item or "vat_paid" in item
        ):
            jurisdiction = str(item.get("jurisdiction", item.get("country", ""))).strip().upper()
            if not jurisdiction:
                raise VatComputationError("Each transaction must include 'jurisdiction'.")
            collected = _to_decimal(item.get("vat_collected", 0), field_name="vat_collected")
            paid = _to_decimal(item.get("vat_paid", 0), field_name="vat_paid")
            signed_vat = _to_money(collected - paid)
        else:
            tx = _coerce_transaction(item)
            jurisdiction = tx.jurisdiction
            signed_vat = tx.vat_amount if tx.transaction_type == SALE else -tx.vat_amount

        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0.00")) + signed_vat

    result: dict[str, Decimal] = {}
    for jurisdiction in sorted(totals):
        total = _to_money(totals[jurisdiction])
        if floor_at_zero and total < 0:
            total = Decimal("0.00")
        result[jurisdiction] = total
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


def generate_vat_summary_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Generate output/input VAT summary and net payable (can be negative)."""
    summary = calculate_vat_position_by_jurisdiction(transactions)
    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction, values in summary.items():
        output_vat = values["output_vat"]
        input_vat = values["input_vat"]
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": _to_money(output_vat - input_vat),
        }
    return result


def generate_vat_to_be_paid_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
    *,
    jurisdiction_key: str = "jurisdiction",
    net_amount_key: str = "net_amount",
    vat_rate_key: str = "vat_rate",
    vat_amount_key: str = "vat_amount",
    jurisdiction_column: str | None = None,
    net_amount_column: str | None = None,
    vat_rate_column: str | None = None,
    vat_amount_column: str | None = None,
) -> dict[str, Decimal]:
    """Generate VAT-to-be-paid amount by jurisdiction.

    Mapping payloads without transaction type are treated as output/sales VAT.
    The final value is floored to zero per jurisdiction.
    """
    if jurisdiction_column is not None:
        jurisdiction_key = jurisdiction_column
    if net_amount_column is not None:
        net_amount_key = net_amount_column
    if vat_rate_column is not None:
        vat_rate_key = vat_rate_column
    if vat_amount_column is not None:
        vat_amount_key = vat_amount_column

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
            if net_amount_key in item and net_amount_key not in {"net_amount", "taxable_amount", "amount"}:
                proxy["net_amount"] = item[net_amount_key]
            if vat_rate_key in item and vat_rate_key not in {"vat_rate", "tax_rate"}:
                proxy["vat_rate"] = item[vat_rate_key]

            # Support custom net_amount key when no canonical key exists.
            if (
                "vat_amount" not in proxy
                and "net_amount" not in proxy
                and "taxable_amount" not in proxy
                and "amount" not in proxy
                and net_amount_key in item
            ):
                proxy["net_amount"] = item[net_amount_key]
            if "vat_amount" not in proxy and "vat_rate" not in proxy and vat_rate_key in item:
                proxy["vat_rate"] = item[vat_rate_key]

            amount = calculate_transaction_vat(proxy)
            tx_raw = item.get(
                "transaction_type",
                item.get("type", item.get("kind", item.get("tax_direction", ""))),
            )
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
    """Compatibility alias for 'for each jurisdiction' phrasing."""
    return generate_vat_to_be_paid_by_jurisdiction(transactions)


def generate_vat_payable_per_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Compatibility alias returning net payable (can be negative)."""
    raw = calculate_vat_payable_by_jurisdiction(transactions)
    if isinstance(raw, dict) and raw and isinstance(next(iter(raw.values())), dict):
        # Defensive fallback; this alias is expected to return simple net values.
        simple: dict[str, Decimal] = {}
        for jurisdiction, totals in raw.items():  # type: ignore[assignment]
            simple[jurisdiction] = _to_money(totals["vat_payable"])  # type: ignore[index]
        return simple
    return raw  # type: ignore[return-value]


def _jurisdiction_column(fieldnames: list[str]) -> str:
    lowered = {name.lower(): name for name in fieldnames}
    if "jurisdiction" in lowered:
        return lowered["jurisdiction"]
    if "country" in lowered:
        return lowered["country"]
    raise VatComputationError(
        "Input CSV must include either 'jurisdiction' or 'country' column."
    )


def _generate_vat_payable_csv(input_path: Path, output_path: Path) -> None:
    """CSV mode used by compatibility tests with revenue/vat_collected input."""
    totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "total_revenue": Decimal("0.00"),
            "total_vat_collected": Decimal("0.00"),
            "total_expected_vat": Decimal("0.00"),
        }
    )

    with input_path.open("r", newline="", encoding="utf-8") as input_file:
        reader = csv.DictReader(input_file)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise VatComputationError("Input CSV must include a header row.")

        jurisdiction_key = _jurisdiction_column(fieldnames)
        required = {"transaction_id", "revenue", "vat_collected", jurisdiction_key}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise VatComputationError(f"Missing required columns: {missing}")

        for row in reader:
            jurisdiction = str(row.get(jurisdiction_key, "")).strip().upper()
            if jurisdiction not in CSV_VAT_RATES:
                raise VatComputationError(f"Unsupported jurisdiction code: {jurisdiction}")

            revenue = _to_decimal(row.get("revenue"), field_name="revenue")
            vat_collected = _to_decimal(
                row.get("vat_collected"), field_name="vat_collected"
            )
            expected_vat = revenue * CSV_VAT_RATES[jurisdiction]

            totals[jurisdiction]["total_revenue"] += revenue
            totals[jurisdiction]["total_vat_collected"] += vat_collected
            totals[jurisdiction]["total_expected_vat"] += expected_vat

    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=[
                "jurisdiction",
                "total_revenue",
                "total_vat_collected",
                "total_expected_vat",
                "vat_to_be_paid",
            ],
        )
        writer.writeheader()
        for jurisdiction in sorted(totals):
            jurisdiction_totals = totals[jurisdiction]
            vat_to_be_paid = (
                jurisdiction_totals["total_expected_vat"]
                - jurisdiction_totals["total_vat_collected"]
            )
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "total_revenue": f"{_to_money(jurisdiction_totals['total_revenue']):.2f}",
                    "total_vat_collected": (
                        f"{_to_money(jurisdiction_totals['total_vat_collected']):.2f}"
                    ),
                    "total_expected_vat": (
                        f"{_to_money(jurisdiction_totals['total_expected_vat']):.2f}"
                    ),
                    "vat_to_be_paid": f"{_to_money(vat_to_be_paid):.2f}",
                }
            )


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]] | str | Path,
    output_path: str | Path | None = None,
    *,
    floor_at_zero: bool = False,
) -> VATPayableResult | None:
    """Generate a detailed VAT summary by jurisdiction."""
    if isinstance(transactions, (str, Path)):
        out_path = Path(output_path) if output_path is not None else Path(
            "vat_payable_by_jurisdiction.csv"
        )
        _generate_vat_payable_csv(Path(transactions), out_path)
        return None

    tx_list = list(transactions)
    if _looks_like_amount_ex_vat_payload(tx_list):
        net = calculate_vat_payable_by_jurisdiction(tx_list, floor_at_zero=floor_at_zero)
        if isinstance(net, list):
            # Defensive: this branch is not expected for amount_ex_vat/net payloads.
            mapped = {row.jurisdiction: row.net_vat for row in net}
            return _build_structured_result(mapped)
        if isinstance(net, dict) and net and isinstance(next(iter(net.values())), dict):
            mapped = {
                jurisdiction: _to_money(values["vat_payable"])
                for jurisdiction, values in net.items()
            }
            return _build_structured_result(mapped)
        return _build_structured_result(net if isinstance(net, dict) else {})

    output_input: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )

    for item in tx_list:
        if isinstance(item, Mapping) and (
            "vat_collected" in item or "vat_paid" in item
        ):
            jurisdiction = str(item.get("jurisdiction", item.get("country", ""))).strip().upper()
            if not jurisdiction:
                raise VatComputationError("Missing required field: jurisdiction")
            output_input[jurisdiction]["output_vat"] += _to_decimal(
                item.get("vat_collected", 0), field_name="vat_collected"
            )
            output_input[jurisdiction]["input_vat"] += _to_decimal(
                item.get("vat_paid", 0), field_name="vat_paid"
            )
            continue

        if isinstance(item, Transaction):
            jurisdiction = item.jurisdiction
            tx_type = _normalize_transaction_type(item.transaction_type, required=True)
            amount = item.vat_amount
        elif isinstance(item, Mapping):
            jurisdiction = str(item.get("jurisdiction", item.get("country", ""))).strip()
            if not jurisdiction:
                raise VatComputationError("Missing required field: jurisdiction")
            tx_type = _extract_transaction_type(item, required=True)
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
        if floor_at_zero and net_vat < 0:
            net_vat = Decimal("0.00")
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


def write_summary_to_csv(
    summary: Mapping[str, Mapping[str, Decimal]],
    output_path: str | Path,
) -> None:
    """Write summary rows to CSV using common output columns."""
    path = Path(output_path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["jurisdiction", "output_vat", "input_vat", "vat_payable"]
        )
        writer.writeheader()
        for jurisdiction in sorted(summary):
            row = summary[jurisdiction]
            writer.writerow(
                {
                    "jurisdiction": jurisdiction,
                    "output_vat": f"{_to_money(row['output_vat']):.2f}",
                    "input_vat": f"{_to_money(row['input_vat']):.2f}",
                    "vat_payable": f"{_to_money(row['vat_payable']):.2f}",
                }
            )


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT payable amount for each jurisdiction."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        help="Path to input JSON file with jurisdiction VAT records.",
    )
    parser.add_argument(
        "--input",
        dest="input_opt",
        type=Path,
        help="Path to input JSON file with jurisdiction VAT records.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output CSV path when input is CSV.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = _parse_args()
    input_file = args.input_file or args.input_opt
    if input_file is None:
        raise SystemExit("Provide input file as positional argument or --input.")

    if input_file.suffix.lower() == ".csv":
        if args.output is not None:
            generate_vat_payable_by_jurisdiction(input_file, args.output)
            return

        rows = read_transactions_from_csv(input_file)
        result = generate_vat_payable_by_jurisdiction(rows)
        payload = {
            jurisdiction: {
                "output_vat": f"{summary.output_vat:.2f}",
                "input_vat": f"{summary.input_vat:.2f}",
                "net_vat": f"{summary.net_vat:.2f}",
                "vat_payable": f"{summary.vat_payable:.2f}",
                "vat_refundable": f"{summary.vat_refundable:.2f}",
            }
            for jurisdiction, summary in result.items()
        }
        print(json.dumps(payload, sort_keys=True))
        return

    records = _load_records(input_file)
    result = vat_payable_by_jurisdiction(records)
    print(json.dumps(result, sort_keys=True))


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
    "VATTransaction",
    "Transaction",
    "VatComputationError",
    "calculate_transaction_vat",
    "CalculateVatSummary",
    "calculate_vat_payable_by_jurisdiction",
    "calculate_vat_position_by_jurisdiction",
    "generate_vat_payable_by_jurisdiction",
    "generate_vat_payable_per_jurisdiction",
    "generate_vat_summary_by_jurisdiction",
    "generate_vat_to_be_paid_by_jurisdiction",
    "generate_vat_to_be_paid_for_each_jurisdiction",
    "load_transactions",
    "read_transactions_from_csv",
    "transaction_from_mapping",
    "transaction_from_record",
    "vat_payable_by_jurisdiction",
    "write_summary_to_csv",
]
