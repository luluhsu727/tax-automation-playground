"""VAT payable calculation utilities grouped by jurisdiction.

The module supports multiple transaction shapes that appear across automation
tasks:
- explicit VAT amounts (``vat_amount``)
- taxable amount + VAT rate (``amount``/``net_amount`` + ``vat_rate``)
- output/input aggregates (``vat_collected`` and ``vat_paid``)
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping

MONEY_PLACES = Decimal("0.01")
TWOPLACES = MONEY_PLACES
SALE = "sale"
PURCHASE = "purchase"
VALID_TRANSACTION_TYPES = {SALE, PURCHASE}

_SALE_ALIASES = {"sale", "sales", "output", "collected", "invoice"}
_PURCHASE_ALIASES = {"purchase", "purchases", "input", "expense", "cost", "bill"}


class VatComputationError(ValueError):
    """Raised when VAT transaction data is invalid."""


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    try:
        text = str(value).strip()
        if text.endswith("%"):
            text = text[:-1].strip()
        return Decimal(text)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise VatComputationError(
            f"Invalid decimal value for '{field_name}': {value!r}"
        ) from exc


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


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


def _extract_transaction_type(record: Mapping[str, Any], *, required: bool) -> str:
    if "tax_direction" in record and record.get("tax_direction") not in (None, ""):
        return _normalize_transaction_type(record.get("tax_direction"), required=True)
    raw = record.get("transaction_type", record.get("type", record.get("kind", "")))
    return _normalize_transaction_type(raw, required=required)


def calculate_transaction_vat(record: Mapping[str, Any]) -> Decimal:
    """Calculate VAT value from vat_amount or amount/rate fields."""
    if "vat_amount" in record and record.get("vat_amount") not in (None, ""):
        vat_amount = _to_decimal(record["vat_amount"], field_name="vat_amount")
    else:
        amount_key: str | None = None
        for key in ("taxable_amount", "net_amount", "amount_ex_vat", "amount"):
            if key in record and record.get(key) not in (None, ""):
                amount_key = key
                break

        rate_key: str | None = None
        for key in ("vat_rate", "tax_rate"):
            if key in record and record.get(key) not in (None, ""):
                rate_key = key
                break

        if amount_key is None or rate_key is None:
            raise VatComputationError(
                "Transaction must provide 'vat_amount' or both amount and VAT rate."
            )

        taxable_amount = _to_decimal(record[amount_key], field_name=amount_key)
        vat_rate = _normalize_rate(_to_decimal(record[rate_key], field_name=rate_key))
        vat_amount = taxable_amount * vat_rate

    if vat_amount < 0:
        raise VatComputationError("VAT amount cannot be negative.")
    return _to_money(vat_amount)


@dataclass(frozen=True)
class Transaction:
    jurisdiction: str
    transaction_type: str
    vat_amount: Decimal
    net_amount: Decimal = Decimal("0.00")
    vat_rate: Decimal = Decimal("0.00")
    taxable: bool = True

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "Transaction":
        jurisdiction = str(record.get("jurisdiction", record.get("country", ""))).strip()
        if not jurisdiction:
            raise VatComputationError("Record is missing a non-empty 'jurisdiction'.")

        tx_type = _extract_transaction_type(record, required=False)
        taxable = _to_bool(record.get("taxable", True))

        net_amount = Decimal("0.00")
        vat_rate = Decimal("0.00")
        for key in ("taxable_amount", "net_amount", "amount_ex_vat", "amount"):
            if key in record and record.get(key) not in (None, ""):
                net_amount = _to_decimal(record[key], field_name=key)
                break
        for key in ("vat_rate", "tax_rate"):
            if key in record and record.get(key) not in (None, ""):
                vat_rate = _normalize_rate(_to_decimal(record[key], field_name=key))
                break

        vat_amount = calculate_transaction_vat(record)
        if not taxable:
            vat_amount = Decimal("0.00")

        return cls(
            jurisdiction=jurisdiction.upper(),
            transaction_type=tx_type,
            vat_amount=vat_amount,
            net_amount=_to_money(net_amount),
            vat_rate=vat_rate,
            taxable=taxable,
        )


class VATSummary(dict[str, Decimal]):
    """Dict-like VAT row with compatibility aliases."""

    def __init__(self, *, output_vat: Decimal, input_vat: Decimal) -> None:
        output_vat = _to_money(output_vat)
        input_vat = _to_money(input_vat)
        net_vat = _to_money(output_vat - input_vat)
        vat_payable = _to_money(net_vat if net_vat > 0 else Decimal("0.00"))
        vat_refundable = _to_money(-net_vat if net_vat < 0 else Decimal("0.00"))
        super().__init__(
            output_vat=output_vat,
            input_vat=input_vat,
            net_vat=net_vat,
            vat_payable=vat_payable,
            vat_refundable=vat_refundable,
            vat_to_be_paid=vat_payable,
            vat_credit=vat_refundable,
        )

    def __getitem__(self, key: str) -> Decimal:
        if key == "vat_to_be_paid":
            key = "vat_payable"
        elif key == "vat_credit":
            key = "vat_refundable"
        return super().__getitem__(key)

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


class VATPayableResult(dict[str, VATSummary]):
    """Dictionary result with list-like compatibility for row access."""

    def __init__(self, rows: Mapping[str, VATSummary]) -> None:
        ordered = dict(sorted(rows.items()))
        super().__init__(ordered)
        self._as_rows = [
            {
                "jurisdiction": jurisdiction,
                "output_vat": summary.output_vat,
                "input_vat": summary.input_vat,
                "net_vat": summary.net_vat,
                "vat_payable": summary.vat_payable,
                "vat_refundable": summary.vat_refundable,
                "vat_to_be_paid": summary["vat_to_be_paid"],
                "vat_credit": summary["vat_credit"],
            }
            for jurisdiction, summary in ordered.items()
        ]

    def __getitem__(self, key: object) -> Any:
        if isinstance(key, int):
            return self._as_rows[key]
        return super().__getitem__(key)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, list):
            if len(other) != len(self._as_rows):
                return False
            for actual, expected in zip(self._as_rows, other):
                if not isinstance(expected, Mapping):
                    return False
                for exp_key, exp_value in expected.items():
                    if actual.get(exp_key) != exp_value:
                        return False
            return True
        return super().__eq__(other)


def transaction_from_record(record: Mapping[str, Any]) -> Transaction:
    return Transaction.from_mapping(record)


def transaction_from_mapping(raw: Mapping[str, Any]) -> Transaction:
    return transaction_from_record(raw)


def _coerce_transaction(item: Transaction | Mapping[str, Any]) -> Transaction:
    if isinstance(item, Transaction):
        return item
    if isinstance(item, Mapping):
        return transaction_from_mapping(item)
    raise VatComputationError("Each transaction must be a Transaction or mapping payload.")


def _accumulate_output_input(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    buckets: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"output_vat": Decimal("0.00"), "input_vat": Decimal("0.00")}
    )
    for item in transactions:
        if isinstance(item, Mapping) and (
            "vat_collected" in item or "vat_paid" in item
        ):
            jurisdiction = str(item.get("jurisdiction", item.get("country", ""))).strip()
            if not jurisdiction:
                raise VatComputationError("Missing required field: jurisdiction")
            buckets[jurisdiction.upper()]["output_vat"] += _to_decimal(
                item.get("vat_collected", 0), field_name="vat_collected"
            )
            buckets[jurisdiction.upper()]["input_vat"] += _to_decimal(
                item.get("vat_paid", 0), field_name="vat_paid"
            )
            continue

        tx = _coerce_transaction(item)
        if tx.transaction_type == SALE:
            buckets[tx.jurisdiction]["output_vat"] += tx.vat_amount
        else:
            buckets[tx.jurisdiction]["input_vat"] += tx.vat_amount

    return buckets


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
    vat_rates_by_jurisdiction: Mapping[str, Any] | None = None,
    *,
    floor_at_zero: bool = False,
) -> dict[str, Decimal] | dict[str, dict[str, Decimal]]:
    """Calculate VAT payable by jurisdiction.

    Default return shape:
      ``{"DE": Decimal("142.50"), ...}`` (net output VAT minus input VAT)

    When ``vat_rates_by_jurisdiction`` is provided, a detailed dictionary is
    returned with taxable sales/purchases and output/input/payable VAT.
    """
    tx_list = list(transactions)

    if vat_rates_by_jurisdiction is not None:
        rates = {
            str(jurisdiction).upper(): _normalize_rate(
                _to_decimal(value, field_name=f"vat rate for {jurisdiction}")
            )
            for jurisdiction, value in vat_rates_by_jurisdiction.items()
        }

        detailed: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {
                "taxable_sales": Decimal("0.00"),
                "taxable_purchases": Decimal("0.00"),
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
            }
        )
        for item in tx_list:
            if isinstance(item, Transaction):
                jurisdiction = item.jurisdiction
                tx_type = item.transaction_type
                base_amount = item.net_amount
                if item.vat_rate == 0 and base_amount != 0 and jurisdiction in rates:
                    vat_amount = _to_money(base_amount * rates[jurisdiction])
                else:
                    vat_amount = item.vat_amount
            elif isinstance(item, Mapping):
                jurisdiction = str(
                    item.get("jurisdiction", item.get("country", ""))
                ).strip().upper()
                if not jurisdiction:
                    raise VatComputationError(f"Transaction missing jurisdiction: {item!r}")
                tx_type = _extract_transaction_type(item, required=True)

                amount_key = None
                for key in ("amount", "net_amount", "taxable_amount", "amount_ex_vat"):
                    if key in item and item.get(key) not in (None, ""):
                        amount_key = key
                        break
                if amount_key is None:
                    raise VatComputationError(f"Invalid amount in transaction: {item!r}")
                base_amount = _to_decimal(item.get(amount_key), field_name=amount_key)

                if "vat_amount" in item and item.get("vat_amount") not in (None, ""):
                    vat_amount = _to_money(
                        _to_decimal(item.get("vat_amount"), field_name="vat_amount")
                    )
                else:
                    rate_value = item.get("vat_rate", item.get("tax_rate"))
                    if rate_value is None:
                        if jurisdiction not in rates:
                            raise VatComputationError(
                                f"No default VAT rate configured for {jurisdiction!r}"
                            )
                        rate = rates[jurisdiction]
                    else:
                        rate = _normalize_rate(
                            _to_decimal(rate_value, field_name="vat_rate")
                        )
                    vat_amount = _to_money(base_amount * rate)
            else:
                raise VatComputationError(
                    "Each transaction must be a Transaction or mapping payload."
                )

            bucket = detailed[jurisdiction]
            if tx_type == SALE:
                bucket["taxable_sales"] += base_amount
                bucket["output_vat"] += vat_amount
            else:
                bucket["taxable_purchases"] += base_amount
                bucket["input_vat"] += vat_amount

        result: dict[str, dict[str, Decimal]] = {}
        for jurisdiction in sorted(detailed):
            totals = detailed[jurisdiction]
            output_vat = _to_money(totals["output_vat"])
            input_vat = _to_money(totals["input_vat"])
            vat_payable = _to_money(output_vat - input_vat)
            result[jurisdiction] = {
                "taxable_sales": _to_money(totals["taxable_sales"]),
                "taxable_purchases": _to_money(totals["taxable_purchases"]),
                "output_vat": output_vat,
                "input_vat": input_vat,
                "vat_payable": vat_payable,
            }
        return result

    buckets = _accumulate_output_input(tx_list)
    result_simple: dict[str, Decimal] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _to_money(buckets[jurisdiction]["output_vat"])
        input_vat = _to_money(buckets[jurisdiction]["input_vat"])
        net = _to_money(output_vat - input_vat)
        if floor_at_zero and net < 0:
            net = Decimal("0.00")
        result_simple[jurisdiction] = net
    return result_simple


def calculate_vat_position_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Return output/input VAT plus payable/credit split by jurisdiction."""
    buckets = _accumulate_output_input(transactions)
    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _to_money(buckets[jurisdiction]["output_vat"])
        input_vat = _to_money(buckets[jurisdiction]["input_vat"])
        net = _to_money(output_vat - input_vat)
        payable = _to_money(net if net > 0 else Decimal("0.00"))
        credit = _to_money(-net if net < 0 else Decimal("0.00"))
        result[jurisdiction] = {
            "output_vat": output_vat,
            "input_vat": input_vat,
            "vat_payable": payable,
            "vat_credit": credit,
        }
    return result


def generate_vat_summary_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, dict[str, Decimal]]:
    """Return output/input VAT and net payable (can be negative)."""
    buckets = _accumulate_output_input(transactions)
    result: dict[str, dict[str, Decimal]] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _to_money(buckets[jurisdiction]["output_vat"])
        input_vat = _to_money(buckets[jurisdiction]["input_vat"])
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
    """Generate VAT-to-be-paid amount per jurisdiction (floored at zero)."""
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
            tx_type = item.transaction_type
            vat_amount = item.vat_amount
        elif isinstance(item, Mapping):
            jurisdiction = str(
                item.get(jurisdiction_key, item.get("jurisdiction", item.get("country", "")))
            ).strip()
            if not jurisdiction:
                raise VatComputationError("Missing required field: jurisdiction")

            proxy = dict(item)
            if vat_amount_key in item and vat_amount_key != "vat_amount":
                proxy["vat_amount"] = item[vat_amount_key]
            if net_amount_key in item and net_amount_key not in {
                "taxable_amount",
                "net_amount",
                "amount_ex_vat",
                "amount",
            }:
                proxy["net_amount"] = item[net_amount_key]
            if vat_rate_key in item and vat_rate_key not in {"vat_rate", "tax_rate"}:
                proxy["vat_rate"] = item[vat_rate_key]

            vat_amount = calculate_transaction_vat(proxy)
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
            totals[jurisdiction] -= vat_amount
        else:
            totals[jurisdiction] += vat_amount

    return {
        jurisdiction: (_to_money(total) if total > 0 else Decimal("0.00"))
        for jurisdiction, total in sorted(totals.items())
    }


def generate_vat_to_be_paid_for_each_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Compatibility alias for wording 'for each jurisdiction'."""
    return generate_vat_to_be_paid_by_jurisdiction(transactions)


def generate_vat_payable_per_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]],
) -> dict[str, Decimal]:
    """Compatibility alias returning net VAT payable (can be negative)."""
    result = calculate_vat_payable_by_jurisdiction(transactions)
    if isinstance(result, dict) and result:
        first = next(iter(result.values()))
        if isinstance(first, dict):
            return {
                jurisdiction: _to_money(values["vat_payable"])
                for jurisdiction, values in result.items()
            }
    return result  # type: ignore[return-value]


def read_transactions_from_csv(csv_path: str | Path) -> list[dict[str, Any]]:
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            cleaned: dict[str, Any] = {}
            for key, value in row.items():
                if isinstance(value, str):
                    stripped = value.strip()
                    cleaned[key] = None if stripped == "" else stripped
                else:
                    cleaned[key] = value
            rows.append(cleaned)
        return rows


def load_transactions(path: str | Path) -> list[Transaction]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        return [transaction_from_record(row) for row in read_transactions_from_csv(path)]
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise VatComputationError("Input JSON must be an array of transaction records.")
    return [transaction_from_record(item) for item in payload]


def write_summary_to_csv(
    summary: Mapping[str, Mapping[str, Decimal]],
    output_path: str | Path,
) -> None:
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


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Transaction | Mapping[str, Any]] | str | Path,
    output_path: str | Path | None = None,
    *,
    floor_at_zero: bool = False,
) -> VATPayableResult | None:
    """Generate jurisdiction-level VAT summary.

    - If ``transactions`` is a path to CSV, writes a CSV report and returns None.
    - Otherwise returns ``VATPayableResult`` keyed by jurisdiction.
    """
    if isinstance(transactions, (str, Path)):
        rows = read_transactions_from_csv(transactions)
        summary = generate_vat_summary_by_jurisdiction(rows)
        out = Path(output_path) if output_path is not None else Path(
            "vat_payable_by_jurisdiction.csv"
        )
        write_summary_to_csv(summary, out)
        return None

    buckets = _accumulate_output_input(transactions)
    summaries: dict[str, VATSummary] = {}
    for jurisdiction in sorted(buckets):
        output_vat = _to_money(buckets[jurisdiction]["output_vat"])
        input_vat = _to_money(buckets[jurisdiction]["input_vat"])
        if floor_at_zero and output_vat < input_vat:
            input_vat = output_vat
        summaries[jurisdiction] = VATSummary(output_vat=output_vat, input_vat=input_vat)
    return VATPayableResult(summaries)


def vat_payable_by_jurisdiction(records: list[dict[str, Any]]) -> dict[str, float]:
    """Alternative API using output/input-style records with float results."""
    output_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    input_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for record in records:
        jurisdiction = record.get("jurisdiction")
        if not jurisdiction or not isinstance(jurisdiction, str):
            raise VatComputationError(f"Invalid jurisdiction in record: {record!r}")

        if "output_vat" in record and record.get("output_vat") not in (None, ""):
            output_vat = _to_decimal(record["output_vat"], field_name="output_vat")
        else:
            sales_amount = _to_decimal(record.get("sales_amount", 0), field_name="sales_amount")
            vat_rate = _normalize_rate(_to_decimal(record.get("vat_rate", 0), field_name="vat_rate"))
            output_vat = sales_amount * vat_rate

        if "input_vat" in record and record.get("input_vat") not in (None, ""):
            input_vat = _to_decimal(record["input_vat"], field_name="input_vat")
        else:
            purchase_amount = _to_decimal(
                record.get("purchase_amount", 0), field_name="purchase_amount"
            )
            deductible_vat_rate = _normalize_rate(
                _to_decimal(
                    record.get("deductible_vat_rate", 0), field_name="deductible_vat_rate"
                )
            )
            input_vat = purchase_amount * deductible_vat_rate

        output_totals[jurisdiction] += output_vat
        input_totals[jurisdiction] += input_vat

    result: dict[str, float] = {}
    for jurisdiction in sorted(set(output_totals) | set(input_totals)):
        payable = output_totals[jurisdiction] - input_totals[jurisdiction]
        payable = max(payable, Decimal("0.00"))
        result[jurisdiction] = float(_to_money(payable))
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate VAT to be paid for each jurisdiction."
    )
    parser.add_argument("input_file", nargs="?", help="Path to transaction JSON or CSV.")
    parser.add_argument("--input", dest="input_opt", help="Path to transaction JSON or CSV.")
    parser.add_argument(
        "--output",
        help="Optional output CSV path (for CSV input modes).",
    )
    parser.add_argument(
        "--output-csv",
        help="Optional output CSV path (alias for --output).",
    )
    parser.add_argument(
        "--floor-at-zero",
        action="store_true",
        help="Floor negative net VAT at 0.00 per jurisdiction.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_file = args.input_file or args.input_opt
    if not input_file:
        raise SystemExit("Provide input file as positional argument or --input.")

    input_path = Path(input_file)
    output_path = args.output_csv or args.output

    if input_path.suffix.lower() == ".csv":
        if output_path:
            generate_vat_payable_by_jurisdiction(input_path, output_path)
            return
        rows = read_transactions_from_csv(input_path)
        summary = generate_vat_payable_by_jurisdiction(
            rows, floor_at_zero=args.floor_at_zero
        )
        payload = {
            jurisdiction: {
                "output_vat": f"{row.output_vat:.2f}",
                "input_vat": f"{row.input_vat:.2f}",
                "net_vat": f"{row.net_vat:.2f}",
                "vat_payable": f"{row.vat_payable:.2f}",
                "vat_refundable": f"{row.vat_refundable:.2f}",
            }
            for jurisdiction, row in (summary or {}).items()
        }
        print(json.dumps(payload, sort_keys=True))
        return

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise VatComputationError("Input JSON must be an array of records.")
    result = generate_vat_to_be_paid_by_jurisdiction(payload)
    printable = {jurisdiction: f"{amount:.2f}" for jurisdiction, amount in result.items()}
    print(json.dumps(printable, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = [
    "MONEY_PLACES",
    "PURCHASE",
    "SALE",
    "TWOPLACES",
    "VALID_TRANSACTION_TYPES",
    "Transaction",
    "VATPayableResult",
    "VATSummary",
    "VatComputationError",
    "calculate_transaction_vat",
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
