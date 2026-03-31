from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping


TWOPLACES = Decimal("0.01")
OUTPUT_KINDS = {"sale", "output", "output_vat", "collected_vat"}
INPUT_KINDS = {"purchase", "input", "input_vat", "paid_vat"}


def _to_decimal(value: Any, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid numeric value for '{field_name}': {value!r}") from exc


def _normalize_kind(raw_kind: Any) -> str:
    if not isinstance(raw_kind, str) or not raw_kind.strip():
        raise ValueError("Each transaction must include a non-empty string 'kind'")

    kind = raw_kind.strip().lower()
    if kind in OUTPUT_KINDS:
        return "output"
    if kind in INPUT_KINDS:
        return "input"
    raise ValueError(
        f"Unknown transaction kind {raw_kind!r}. "
        f"Supported output kinds: {sorted(OUTPUT_KINDS)}; input kinds: {sorted(INPUT_KINDS)}"
    )


def _compute_vat_amount(transaction: Mapping[str, Any]) -> Decimal:
    if "vat_amount" in transaction and transaction["vat_amount"] is not None:
        vat_amount = _to_decimal(transaction["vat_amount"], "vat_amount")
    else:
        if "amount" not in transaction:
            raise ValueError("Transaction must include either 'vat_amount' or both 'amount' and 'vat_rate'")
        if "vat_rate" not in transaction:
            raise ValueError("Transaction must include either 'vat_amount' or both 'amount' and 'vat_rate'")
        amount = _to_decimal(transaction["amount"], "amount")
        vat_rate = _to_decimal(transaction["vat_rate"], "vat_rate")
        vat_amount = amount * vat_rate

    if vat_amount < 0:
        raise ValueError("VAT amount must be non-negative")
    return vat_amount


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """
    Generate net VAT payable for each jurisdiction.

    Net VAT payable is:
      output VAT (collected on sales)
    - input VAT (paid on purchases)

    Each transaction requires:
      - jurisdiction: str
      - kind: one of {"sale"/"output"/...} or {"purchase"/"input"/...}
      - Either:
          * vat_amount
        Or:
          * amount and vat_rate

    Returns:
      dict[jurisdiction, Decimal] rounded to 2 decimal places.
      Positive => VAT to be paid. Negative => VAT reclaimable.
    """
    totals: dict[str, Decimal] = {}

    for transaction in transactions:
        if not isinstance(transaction, Mapping):
            raise ValueError(f"Each transaction must be a mapping/dict, got {type(transaction)!r}")

        jurisdiction_raw = transaction.get("jurisdiction")
        if not isinstance(jurisdiction_raw, str) or not jurisdiction_raw.strip():
            raise ValueError("Each transaction must include a non-empty string 'jurisdiction'")
        jurisdiction = jurisdiction_raw.strip()

        kind = _normalize_kind(transaction.get("kind"))
        vat_amount = _compute_vat_amount(transaction)

        signed_amount = vat_amount if kind == "output" else -vat_amount
        totals[jurisdiction] = totals.get(jurisdiction, Decimal("0")) + signed_amount

    return {
        jurisdiction: total.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        for jurisdiction, total in totals.items()
    }


def generate_vat_payable_by_jurisdiction(
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Decimal]:
    """
    Alias for calculate_vat_payable_by_jurisdiction.
    """
    return calculate_vat_payable_by_jurisdiction(transactions)
