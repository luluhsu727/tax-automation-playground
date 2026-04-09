from decimal import Decimal

import pytest

from vat.calculator import calculate_vat_payable_by_jurisdiction


def test_calculates_vat_payable_per_jurisdiction() -> None:
    transactions = [
        {"jurisdiction": "DE", "transaction_type": "sale", "net_amount": 1000, "vat_rate": 0.19},
        {"jurisdiction": "DE", "transaction_type": "purchase", "net_amount": 300, "vat_rate": 0.19},
        {"jurisdiction": "FR", "transaction_type": "sale", "vat_amount": 200},
        {"jurisdiction": "FR", "transaction_type": "purchase", "vat_amount": 250},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"].output_vat == Decimal("190.00")
    assert result["DE"].input_vat == Decimal("57.00")
    assert result["DE"].net_vat == Decimal("133.00")
    assert result["DE"].vat_payable == Decimal("133.00")

    assert result["FR"].output_vat == Decimal("200.00")
    assert result["FR"].input_vat == Decimal("250.00")
    assert result["FR"].net_vat == Decimal("-50.00")
    assert result["FR"].vat_payable == Decimal("0.00")


def test_accepts_percentage_vat_rate() -> None:
    result = calculate_vat_payable_by_jurisdiction(
        [{"jurisdiction": "GB", "transaction_type": "sale", "net_amount": "150", "vat_rate": "20"}]
    )

    assert result["GB"].output_vat == Decimal("30.00")
    assert result["GB"].vat_payable == Decimal("30.00")


def test_requires_jurisdiction() -> None:
    with pytest.raises(ValueError, match="jurisdiction is required"):
        calculate_vat_payable_by_jurisdiction(
            [{"transaction_type": "sale", "net_amount": 100, "vat_rate": 0.2}]
        )
