from decimal import Decimal

import pytest

from vat_payable.calculator import calculate_vat_payable_by_jurisdiction, serialize_totals


def test_calculates_vat_payable_per_jurisdiction() -> None:
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "vat_amount": "120.00"},
        {"jurisdiction": "DE", "type": "purchase", "vat_amount": "20.00"},
        {"jurisdiction": "FR", "type": "sale", "vat_amount": "50"},
        {"jurisdiction": "FR", "type": "input", "vat_amount": "70"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {"DE": Decimal("100.00"), "FR": Decimal("-20.00")}


def test_computes_vat_amount_from_rate_supporting_percent_or_fraction() -> None:
    transactions = [
        {"jurisdiction": "ES", "type": "output", "amount": "1000", "vat_rate": "21"},
        {"jurisdiction": "ES", "type": "deductible", "amount": "200", "vat_rate": "0.21"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {"ES": Decimal("168.00")}


def test_raises_for_unsupported_transaction_type() -> None:
    with pytest.raises(ValueError, match="Unsupported transaction type"):
        calculate_vat_payable_by_jurisdiction(
            [{"jurisdiction": "IT", "type": "refund", "vat_amount": "10"}]
        )


def test_raises_for_missing_jurisdiction() -> None:
    with pytest.raises(ValueError, match="Invalid 'jurisdiction'"):
        calculate_vat_payable_by_jurisdiction([{"type": "sale", "vat_amount": "10"}])


def test_serialize_totals() -> None:
    serialized = serialize_totals({"DE": Decimal("12"), "FR": Decimal("-3.5")})
    assert serialized == {"DE": "12.00", "FR": "-3.50"}
