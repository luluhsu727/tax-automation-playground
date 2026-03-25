from decimal import Decimal

import pytest

from vat_payable import (
    calculate_vat_payable_by_jurisdiction,
    vat_to_be_paid_by_jurisdiction,
)


def test_calculate_vat_payable_by_jurisdiction_mixed_positions() -> None:
    transactions = [
        {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "0.19", "kind": "sale"},
        {"jurisdiction": "DE", "amount": "40.00", "vat_rate": "0.19", "kind": "purchase"},
        {"jurisdiction": "FR", "amount": "50.00", "vat_rate": "0.20", "kind": "purchase"},
        {"jurisdiction": "FR", "amount": "20.00", "vat_rate": "0.20", "kind": "sale"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"].output_vat == Decimal("19.00")
    assert result["DE"].input_vat == Decimal("7.60")
    assert result["DE"].net_vat == Decimal("11.40")
    assert result["DE"].payable_vat == Decimal("11.40")
    assert result["DE"].refundable_vat == Decimal("0.00")

    assert result["FR"].output_vat == Decimal("4.00")
    assert result["FR"].input_vat == Decimal("10.00")
    assert result["FR"].net_vat == Decimal("-6.00")
    assert result["FR"].payable_vat == Decimal("0.00")
    assert result["FR"].refundable_vat == Decimal("6.00")


def test_vat_to_be_paid_by_jurisdiction_returns_only_positive_payable() -> None:
    transactions = [
        {"jurisdiction": "ES", "amount": "99.99", "vat_rate": "0.21", "kind": "sale"},
        {"jurisdiction": "ES", "amount": "30", "vat_rate": "0.21", "kind": "purchase"},
        {"jurisdiction": "IT", "amount": "150", "vat_rate": "0.22", "kind": "purchase"},
    ]

    payable = vat_to_be_paid_by_jurisdiction(transactions)
    assert payable == {"ES": Decimal("14.70"), "IT": Decimal("0.00")}


def test_invalid_kind_raises_value_error() -> None:
    transactions = [
        {"jurisdiction": "NL", "amount": "10", "vat_rate": "0.21", "kind": "refund"}
    ]
    with pytest.raises(ValueError, match="invalid kind"):
        calculate_vat_payable_by_jurisdiction(transactions)

