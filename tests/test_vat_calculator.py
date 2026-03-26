from decimal import Decimal

import pytest

from vat_calculator import generate_vat_payable_by_jurisdiction


def test_generates_vat_payable_by_jurisdiction_with_mixed_transactions():
    transactions = [
        {
            "jurisdiction": "DE",
            "transaction_type": "sale",
            "vat_amount": "19.00",
        },
        {
            "jurisdiction": "DE",
            "transaction_type": "purchase",
            "vat_amount": "4.00",
        },
        {
            "jurisdiction": "FR",
            "transaction_type": "sale",
            "amount": "100.00",
            "vat_rate": "0.20",
        },
        {
            "jurisdiction": "FR",
            "transaction_type": "input",
            "amount": "80.00",
            "vat_rate": "0.20",
        },
    ]

    result = generate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"] == {
        "output_vat": Decimal("19.00"),
        "input_vat": Decimal("4.00"),
        "net_vat": Decimal("15.00"),
        "vat_payable": Decimal("15.00"),
        "vat_refundable": Decimal("0.00"),
    }
    assert result["FR"] == {
        "output_vat": Decimal("20.00"),
        "input_vat": Decimal("16.00"),
        "net_vat": Decimal("4.00"),
        "vat_payable": Decimal("4.00"),
        "vat_refundable": Decimal("0.00"),
    }


def test_refundable_jurisdiction_is_reported_when_input_exceeds_output():
    transactions = [
        {
            "jurisdiction": "ES",
            "transaction_type": "sale",
            "vat_amount": "10.00",
        },
        {
            "jurisdiction": "ES",
            "transaction_type": "purchase",
            "vat_amount": "12.50",
        },
    ]

    result = generate_vat_payable_by_jurisdiction(transactions)

    assert result["ES"]["net_vat"] == Decimal("-2.50")
    assert result["ES"]["vat_payable"] == Decimal("0.00")
    assert result["ES"]["vat_refundable"] == Decimal("2.50")


def test_missing_jurisdiction_raises_value_error():
    with pytest.raises(ValueError, match="missing 'jurisdiction'"):
        generate_vat_payable_by_jurisdiction(
            [{"transaction_type": "sale", "vat_amount": "1.00"}]
        )


def test_invalid_transaction_type_raises_value_error():
    with pytest.raises(ValueError, match="invalid 'transaction_type'"):
        generate_vat_payable_by_jurisdiction(
            [
                {
                    "jurisdiction": "IT",
                    "transaction_type": "refund",
                    "vat_amount": "1.00",
                }
            ]
        )
