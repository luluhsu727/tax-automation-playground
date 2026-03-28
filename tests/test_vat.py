from decimal import Decimal

import pytest

from vat_automation.vat import (
    VatTransaction,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_by_jurisdiction,
)


def test_generate_vat_payable_by_jurisdiction_mixed_transactions() -> None:
    records = [
        {"jurisdiction": "DE", "kind": "sale", "amount": "100.00", "vat_rate": "0.19"},
        {"jurisdiction": "DE", "kind": "purchase", "amount": "10.00", "vat_rate": "0.19"},
        {"jurisdiction": "FR", "kind": "sale", "vat_amount": "8.50"},
        {"jurisdiction": "FR", "kind": "purchase", "vat_amount": "9.00"},
        {"jurisdiction": "ES", "kind": "sale", "vat_amount": "3.333"},
    ]

    result = generate_vat_payable_by_jurisdiction(records)

    assert result == {
        "DE": Decimal("17.10"),
        "ES": Decimal("3.33"),
        "FR": Decimal("0.00"),
    }


def test_calculate_vat_payable_by_jurisdiction_clamps_credit_to_zero() -> None:
    transactions = [
        VatTransaction(jurisdiction="UK", kind="sale", vat_amount=Decimal("2.00")),
        VatTransaction(jurisdiction="UK", kind="purchase", vat_amount=Decimal("5.00")),
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)
    assert result == {"UK": Decimal("0.00")}


@pytest.mark.parametrize(
    "record,error_message",
    [
        (
            {"kind": "sale", "vat_amount": "5.00"},
            "missing 'jurisdiction'",
        ),
        (
            {"jurisdiction": "DE", "kind": "refund", "vat_amount": "5.00"},
            "must be either 'sale' or 'purchase'",
        ),
        (
            {"jurisdiction": "DE", "kind": "sale", "amount": "100.00"},
            "must provide either 'vat_amount' or both 'amount' and 'vat_rate'",
        ),
    ],
)
def test_transaction_validation(record: dict[str, str], error_message: str) -> None:
    with pytest.raises(ValueError, match=error_message):
        VatTransaction.from_record(record)
