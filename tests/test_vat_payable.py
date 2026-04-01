from decimal import Decimal

import pytest

from vat_payable import Transaction, calculate_vat_payable_by_jurisdiction


def test_calculate_vat_payable_multiple_jurisdictions() -> None:
    transactions = [
        Transaction("DE", "sale", "1000", "19"),
        Transaction("DE", "purchase", "200", "19"),
        Transaction("FR", "sale", "500", "20"),
        Transaction("FR", "purchase", "150", "20"),
    ]

    report = calculate_vat_payable_by_jurisdiction(transactions)

    assert report == {
        "DE": {
            "output_vat": Decimal("190.00"),
            "input_vat": Decimal("38.00"),
            "vat_payable": Decimal("152.00"),
        },
        "FR": {
            "output_vat": Decimal("100.00"),
            "input_vat": Decimal("30.00"),
            "vat_payable": Decimal("70.00"),
        },
    }


def test_uses_default_rates_when_missing_on_transaction() -> None:
    transactions = [
        Transaction("ES", "sale", "100"),
        Transaction("ES", "purchase", "50"),
    ]

    report = calculate_vat_payable_by_jurisdiction(transactions, default_rates={"ES": "21"})
    assert report["ES"]["vat_payable"] == Decimal("10.50")


def test_raises_when_rate_missing() -> None:
    with pytest.raises(ValueError, match="Missing VAT rate for jurisdiction"):
        calculate_vat_payable_by_jurisdiction([Transaction("US", "sale", "100")])


def test_rate_can_be_fraction_or_percentage() -> None:
    transactions = [
        Transaction("UK", "sale", "100", "0.2"),
        Transaction("UK", "purchase", "20", "20"),
    ]
    report = calculate_vat_payable_by_jurisdiction(transactions)
    assert report["UK"]["vat_payable"] == Decimal("16.00")
