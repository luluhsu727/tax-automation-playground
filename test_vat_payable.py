from decimal import Decimal

import pytest

from vat_payable import generate_vat_payable_by_jurisdiction


def test_generate_vat_payable_by_jurisdiction_from_net_and_rate() -> None:
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "net_amount": "100.00", "vat_rate": "19"},
        {"jurisdiction": "DE", "type": "purchase", "net_amount": "40.00", "vat_rate": "19"},
        {"jurisdiction": "FR", "type": "sale", "net_amount": "80.00", "vat_rate": "0.20"},
        {"jurisdiction": "FR", "type": "purchase", "net_amount": "20.00", "vat_rate": "20"},
    ]

    result = generate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"] == {
        "output_vat": Decimal("19.00"),
        "input_vat": Decimal("7.60"),
        "vat_payable": Decimal("11.40"),
    }
    assert result["FR"] == {
        "output_vat": Decimal("16.00"),
        "input_vat": Decimal("4.00"),
        "vat_payable": Decimal("12.00"),
    }


def test_generate_vat_payable_by_jurisdiction_with_explicit_vat_amount() -> None:
    transactions = [
        {"jurisdiction": "UK", "type": "sale", "vat_amount": "25.55"},
        {"jurisdiction": "UK", "type": "purchase", "vat_amount": "10.10"},
        {"jurisdiction": "UK", "type": "purchase", "vat_amount": "2.45"},
    ]

    result = generate_vat_payable_by_jurisdiction(transactions)

    assert result["UK"] == {
        "output_vat": Decimal("25.55"),
        "input_vat": Decimal("12.55"),
        "vat_payable": Decimal("13.00"),
    }


@pytest.mark.parametrize(
    "transaction, expected_message",
    [
        ({"type": "sale", "net_amount": "10", "vat_rate": "20"}, "missing 'jurisdiction'"),
        (
            {"jurisdiction": "DE", "type": "refund", "net_amount": "10", "vat_rate": "20"},
            "invalid 'type'",
        ),
        ({"jurisdiction": "DE", "type": "sale", "vat_rate": "20"}, "missing 'net_amount'"),
        ({"jurisdiction": "DE", "type": "sale", "net_amount": "10"}, "missing 'vat_rate'"),
        (
            {"jurisdiction": "DE", "type": "sale", "net_amount": "-1", "vat_rate": "20"},
            "net_amount cannot be negative",
        ),
        (
            {"jurisdiction": "DE", "type": "sale", "net_amount": "10", "vat_rate": "-20"},
            "VAT rate cannot be negative",
        ),
    ],
)
def test_invalid_transaction_validation(transaction, expected_message: str) -> None:
    with pytest.raises(ValueError, match=expected_message):
        generate_vat_payable_by_jurisdiction([transaction])
