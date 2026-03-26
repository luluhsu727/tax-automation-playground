from decimal import Decimal

import pytest

from vat import Transaction, vat_to_be_paid_by_jurisdiction


def test_vat_payable_grouped_by_jurisdiction():
    transactions = [
        Transaction("DE", Decimal("100.00"), Decimal("0.19"), "sale"),
        Transaction("DE", Decimal("40.00"), Decimal("0.19"), "purchase"),
        Transaction("FR", Decimal("200.00"), Decimal("0.20"), "sale"),
        Transaction("FR", Decimal("20.00"), Decimal("0.20"), "purchase"),
    ]

    result = vat_to_be_paid_by_jurisdiction(transactions)

    assert result["DE"]["output_vat"] == Decimal("19.00")
    assert result["DE"]["input_vat"] == Decimal("7.60")
    assert result["DE"]["vat_payable"] == Decimal("11.40")
    assert result["DE"]["vat_credit"] == Decimal("0.00")

    assert result["FR"]["output_vat"] == Decimal("40.00")
    assert result["FR"]["input_vat"] == Decimal("4.00")
    assert result["FR"]["vat_payable"] == Decimal("36.00")
    assert result["FR"]["vat_credit"] == Decimal("0.00")


def test_vat_credit_when_input_exceeds_output():
    transactions = [
        {"jurisdiction": "ES", "amount": "10.00", "vat_rate": "0.21", "kind": "sale"},
        {
            "jurisdiction": "ES",
            "amount": "100.00",
            "vat_rate": "0.21",
            "kind": "purchase",
        },
    ]

    result = vat_to_be_paid_by_jurisdiction(transactions)

    assert result["ES"]["output_vat"] == Decimal("2.10")
    assert result["ES"]["input_vat"] == Decimal("21.00")
    assert result["ES"]["vat_payable"] == Decimal("-18.90")
    assert result["ES"]["vat_credit"] == Decimal("18.90")


def test_invalid_kind_raises():
    with pytest.raises(ValueError, match="Unsupported transaction kind"):
        vat_to_be_paid_by_jurisdiction(
            [{"jurisdiction": "IT", "amount": 100, "vat_rate": 0.22, "kind": "refund"}]
        )


def test_empty_jurisdiction_raises():
    with pytest.raises(ValueError, match="Jurisdiction cannot be empty"):
        vat_to_be_paid_by_jurisdiction(
            [{"jurisdiction": "  ", "amount": 100, "vat_rate": 0.22, "kind": "sale"}]
        )


def test_negative_amount_raises():
    with pytest.raises(ValueError, match="Amount cannot be negative"):
        vat_to_be_paid_by_jurisdiction(
            [{"jurisdiction": "NL", "amount": -1, "vat_rate": 0.21, "kind": "sale"}]
        )
