from decimal import Decimal

import pytest

from vat_payable import calculate_vat_payable_by_jurisdiction


def test_calculates_vat_payable_per_jurisdiction():
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "amount": "100.00"},
        {"jurisdiction": "DE", "type": "purchase", "amount": "25.00"},
        {"jurisdiction": "FR", "type": "sale", "amount": "200.00", "vat_rate": 10},
        {"jurisdiction": "FR", "type": "purchase", "amount": "50.00", "vat_rate": 0.10},
    ]
    rates = {"DE": Decimal("0.19"), "FR": Decimal("0.20")}

    result = calculate_vat_payable_by_jurisdiction(transactions, rates)

    assert result["DE"]["output_vat"] == Decimal("19.00")
    assert result["DE"]["input_vat"] == Decimal("4.75")
    assert result["DE"]["vat_payable"] == Decimal("14.25")

    assert result["FR"]["output_vat"] == Decimal("20.00")
    assert result["FR"]["input_vat"] == Decimal("5.00")
    assert result["FR"]["vat_payable"] == Decimal("15.00")


def test_raises_when_missing_default_rate_and_no_transaction_override():
    with pytest.raises(ValueError, match="No default VAT rate configured"):
        calculate_vat_payable_by_jurisdiction(
            [{"jurisdiction": "ES", "type": "sale", "amount": 100}],
            {},
        )

