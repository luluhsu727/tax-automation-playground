from decimal import Decimal

import pytest

from vat_payable import Transaction, generate_vat_payable_by_jurisdiction


def test_generate_vat_payable_by_jurisdiction_with_global_rates():
    transactions = [
        Transaction("UK", Decimal("100.00"), "sale"),
        Transaction("UK", Decimal("30.00"), "purchase"),
        Transaction("DE", Decimal("100.00"), "sale"),
        Transaction("DE", Decimal("25.00"), "purchase"),
    ]

    summaries = generate_vat_payable_by_jurisdiction(
        transactions, jurisdiction_vat_rates={"UK": "0.20", "DE": "0.19"}
    )

    assert summaries["UK"].output_vat == Decimal("20.00")
    assert summaries["UK"].input_vat == Decimal("6.00")
    assert summaries["UK"].vat_payable == Decimal("14.00")

    assert summaries["DE"].output_vat == Decimal("19.00")
    assert summaries["DE"].input_vat == Decimal("4.75")
    assert summaries["DE"].vat_payable == Decimal("14.25")


def test_transaction_rate_overrides_global_rate():
    transactions = [
        Transaction("UK", Decimal("100.00"), "sale", vat_rate=Decimal("0.05")),
        Transaction("UK", Decimal("50.00"), "purchase"),
    ]

    summaries = generate_vat_payable_by_jurisdiction(
        transactions, jurisdiction_vat_rates={"UK": "0.20"}
    )

    assert summaries["UK"].output_vat == Decimal("5.00")
    assert summaries["UK"].input_vat == Decimal("10.00")
    assert summaries["UK"].vat_payable == Decimal("-5.00")


def test_raises_when_rate_missing():
    with pytest.raises(ValueError, match="Missing VAT rate"):
        generate_vat_payable_by_jurisdiction(
            [Transaction("FR", Decimal("10.00"), "sale")]
        )


def test_raises_on_invalid_inputs():
    with pytest.raises(ValueError, match="negative"):
        generate_vat_payable_by_jurisdiction(
            [Transaction("UK", Decimal("-1.00"), "sale", vat_rate=Decimal("0.2"))]
        )

    with pytest.raises(ValueError, match="sale|purchase"):
        generate_vat_payable_by_jurisdiction(
            [Transaction("UK", Decimal("1.00"), "refund", vat_rate=Decimal("0.2"))]
        )

