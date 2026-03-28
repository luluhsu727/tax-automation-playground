"""VAT calculation helpers for jurisdiction-level payable totals."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping

TWOPLACES = Decimal("0.01")


def _to_decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Invalid decimal value for {field_name}: {value!r}") from exc


def _to_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class VatTransaction:
    """A single VAT-relevant transaction."""

    jurisdiction: str
    vat_amount: Decimal
    kind: str

    def signed_vat(self) -> Decimal:
        """Return signed VAT for net payable math.

        - Sales increase VAT liability.
        - Purchases decrease VAT liability (input credit).
        """
        if self.kind == "sale":
            return self.vat_amount
        if self.kind == "purchase":
            return -self.vat_amount
        raise ValueError(f"Unsupported transaction kind: {self.kind!r}")

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> "VatTransaction":
        """Create a transaction from an input record.

        Required fields:
            - jurisdiction: str
            - kind: "sale" or "purchase"
        And one of:
            - vat_amount
            - amount + vat_rate
        """
        jurisdiction = str(record.get("jurisdiction", "")).strip()
        if not jurisdiction:
            raise ValueError("Transaction is missing 'jurisdiction'.")

        kind = str(record.get("kind", "")).strip().lower()
        if kind not in {"sale", "purchase"}:
            raise ValueError(
                "Transaction field 'kind' must be either 'sale' or 'purchase'."
            )

        if "vat_amount" in record and record["vat_amount"] not in ("", None):
            vat_amount = _to_decimal(record["vat_amount"], "vat_amount")
        else:
            if "amount" not in record or "vat_rate" not in record:
                raise ValueError(
                    "Transaction must provide either 'vat_amount' "
                    "or both 'amount' and 'vat_rate'."
                )
            amount = _to_decimal(record["amount"], "amount")
            vat_rate = _to_decimal(record["vat_rate"], "vat_rate")
            vat_amount = amount * vat_rate

        if vat_amount < 0:
            raise ValueError("'vat_amount' must be non-negative.")

        return cls(
            jurisdiction=jurisdiction,
            vat_amount=_to_money(vat_amount),
            kind=kind,
        )


def calculate_vat_payable_by_jurisdiction(
    transactions: Iterable[VatTransaction],
) -> dict[str, Decimal]:
    """Calculate VAT payable by jurisdiction.

    Returns a mapping of jurisdiction -> payable amount.
    Payable is clamped at 0.00 for jurisdictions with a net credit.
    """
    net_by_jurisdiction: dict[str, Decimal] = {}
    for transaction in transactions:
        current = net_by_jurisdiction.get(transaction.jurisdiction, Decimal("0"))
        net_by_jurisdiction[transaction.jurisdiction] = current + transaction.signed_vat()

    payable_by_jurisdiction: dict[str, Decimal] = {}
    for jurisdiction, net_vat in net_by_jurisdiction.items():
        payable_by_jurisdiction[jurisdiction] = _to_money(max(net_vat, Decimal("0")))

    return dict(sorted(payable_by_jurisdiction.items()))


def generate_vat_payable_by_jurisdiction(
    records: Iterable[Mapping[str, object]],
) -> dict[str, Decimal]:
    """Parse transaction records and generate VAT payable by jurisdiction."""
    transactions = [VatTransaction.from_record(record) for record in records]
    return calculate_vat_payable_by_jurisdiction(transactions)
