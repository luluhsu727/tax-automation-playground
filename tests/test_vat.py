from decimal import Decimal

import pytest

from vat import (
    calculate_vat_to_be_paid_by_jurisdiction,
    generate_vat_to_be_paid_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


def test_calculates_vat_payable_grouped_by_jurisdiction() -> None:
    transactions = [
        {"jurisdiction": "DE", "amount": "100.00", "vat_rate": "19"},
        {"jurisdiction": "DE", "amount": "50.00", "vat_rate": "19"},
        {"jurisdiction": "FR", "amount": "200.00", "vat_rate": "20"},
    ]

    result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

    assert result == {"DE": Decimal("28.50"), "FR": Decimal("40.00")}


def test_handles_decimal_rates_when_explicitly_configured() -> None:
    transactions = [
        {"jurisdiction": "NL", "taxable_amount": 75, "rate": Decimal("0.21")},
        {"jurisdiction": "NL", "taxable_amount": 25, "rate": Decimal("0.21")},
    ]

    result = calculate_vat_to_be_paid_by_jurisdiction(
        transactions,
        amount_key="taxable_amount",
        vat_rate_key="rate",
        rates_are_percentages=False,
    )

    assert result == {"NL": Decimal("21.00")}


def test_negative_amounts_reduce_vat_payable() -> None:
    transactions = [
        {"jurisdiction": "GB", "amount": "100", "vat_rate": "20"},
        {"jurisdiction": "GB", "amount": "-10", "vat_rate": "20"},  # refund/credit note
    ]

    result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

    assert result == {"GB": Decimal("18.00")}


def test_rounds_using_half_up() -> None:
    transactions = [
        {"jurisdiction": "SE", "amount": "0.05", "vat_rate": "10"},
    ]

    result = calculate_vat_to_be_paid_by_jurisdiction(transactions)

    assert result == {"SE": Decimal("0.01")}


def test_alias_functions_delegate_to_primary_implementation() -> None:
    transactions = [{"jurisdiction": "ES", "amount": "100", "vat_rate": "21"}]

    assert generate_vat_to_be_paid_for_each_jurisdiction(transactions) == {
        "ES": Decimal("21.00")
    }
    assert generate_vat_to_be_paid_by_jurisdiction(transactions) == {
        "ES": Decimal("21.00")
    }


def test_raises_for_missing_jurisdiction() -> None:
    with pytest.raises(ValueError, match="missing required key 'jurisdiction'"):
        calculate_vat_to_be_paid_by_jurisdiction(
            [
                {"amount": "100", "vat_rate": "20"},
            ]
        )
