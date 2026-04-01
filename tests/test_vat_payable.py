from decimal import Decimal

import pytest

from vat_payable import generate_vat_payable_by_jurisdiction


def test_generates_vat_payable_by_jurisdiction() -> None:
    transactions = [
        {"jurisdiction": "DE", "transaction_type": "sale", "vat_amount": "19.00"},
        {"jurisdiction": "DE", "transaction_type": "purchase", "vat_amount": "4.00"},
        {"jurisdiction": "FR", "transaction_type": "sale", "net_amount": "100", "vat_rate": "0.20"},
        {"jurisdiction": "FR", "transaction_type": "purchase", "net_amount": "10", "vat_rate": "0.20"},
    ]

    result = generate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"]["output_vat"] == Decimal("19.00")
    assert result["DE"]["input_vat"] == Decimal("4.00")
    assert result["DE"]["vat_payable"] == Decimal("15.00")

    assert result["FR"]["output_vat"] == Decimal("20.00")
    assert result["FR"]["input_vat"] == Decimal("2.00")
    assert result["FR"]["vat_payable"] == Decimal("18.00")


def test_allows_negative_payable_for_refund_scenario() -> None:
    transactions = [
        {"jurisdiction": "NL", "transaction_type": "sale", "vat_amount": "5.00"},
        {"jurisdiction": "NL", "transaction_type": "purchase", "vat_amount": "12.00"},
    ]

    result = generate_vat_payable_by_jurisdiction(transactions)
    assert result["NL"]["vat_payable"] == Decimal("-7.00")


def test_requires_jurisdiction() -> None:
    with pytest.raises(ValueError, match="jurisdiction"):
        generate_vat_payable_by_jurisdiction(
            [{"transaction_type": "sale", "vat_amount": "1.00"}]
        )


def test_requires_valid_transaction_type() -> None:
    with pytest.raises(ValueError, match="sale|purchase"):
        generate_vat_payable_by_jurisdiction(
            [{"jurisdiction": "DE", "transaction_type": "refund", "vat_amount": "1.00"}]
        )
