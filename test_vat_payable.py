from decimal import Decimal

import pytest

from vat_payable import calculate_vat_payable_by_jurisdiction


def test_calculate_vat_payable_by_jurisdiction_with_type_based_transactions():
    transactions = [
        {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "120.00"},
        {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "30.50"},
        {"jurisdiction": "FR", "transaction_type": "sales", "vat_amount": "50"},
        {"jurisdiction": "FR", "transaction_type": "expense", "vat_amount": "10"},
        {"jurisdiction": "FR", "transaction_type": "adjustment", "vat_amount": "-5"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {
        "DE": Decimal("89.50"),
        "FR": Decimal("35.00"),
    }


def test_calculate_vat_payable_by_jurisdiction_with_collected_and_paid_fields():
    transactions = [
        {"jurisdiction": "GB", "vat_collected": "200.25", "vat_paid": "80.15"},
        {"jurisdiction": "GB", "vat_collected": "10.00", "vat_paid": "0"},
        {"jurisdiction": "ES", "vat_collected": "0", "vat_paid": "15.01"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {
        "ES": Decimal("-15.01"),
        "GB": Decimal("130.10"),
    }


def test_raises_when_jurisdiction_missing():
    with pytest.raises(ValueError, match="jurisdiction"):
        calculate_vat_payable_by_jurisdiction(
            [{"transaction_type": "sale", "vat_amount": "10"}]
        )


def test_raises_when_transaction_type_unknown():
    with pytest.raises(ValueError, match="Unsupported transaction_type"):
        calculate_vat_payable_by_jurisdiction(
            [{"jurisdiction": "IT", "transaction_type": "refund", "vat_amount": "10"}]
        )


def test_raises_when_no_vat_fields_present():
    with pytest.raises(ValueError, match="vat_amount"):
        calculate_vat_payable_by_jurisdiction([{"jurisdiction": "IT"}])
