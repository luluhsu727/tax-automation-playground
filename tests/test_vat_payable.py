from decimal import Decimal

import pytest

from vat_payable import (
    VatComputationError,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    vat_payable_by_jurisdiction,
)


def test_generate_vat_to_be_paid_for_each_jurisdiction():
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
        {"jurisdiction": "DE", "type": "purchase", "amount": 250, "vat_rate": 0.19},
        {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
        {"jurisdiction": "FR", "type": "purchase", "amount": 600, "vat_rate": 0.20},
    ]

    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)

    assert result == {"DE": Decimal("142.50"), "FR": Decimal("0.00")}


def test_calculate_vat_payable_supports_collected_and_paid_shape():
    transactions = [
        {"jurisdiction": "DE", "vat_collected": "120.00", "vat_paid": "20.00"},
        {"jurisdiction": "DE", "vat_collected": "45.50", "vat_paid": "5.50"},
        {"jurisdiction": "FR", "vat_collected": "15.00", "vat_paid": "25.00"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {"DE": Decimal("140.00"), "FR": Decimal("-10.00")}


def test_output_input_api_returns_floored_float_values():
    records = [
        {"jurisdiction": "DE", "sales_amount": 1000, "purchase_amount": 200, "vat_rate": 0.19, "deductible_vat_rate": 0.19},
        {"jurisdiction": "FR", "output_vat": 50, "input_vat": 80},
    ]

    result = vat_payable_by_jurisdiction(records)

    assert result == {"DE": 152.0, "FR": 0.0}


def test_invalid_transaction_type_raises():
    transactions = [{"jurisdiction": "DE", "type": "refund", "amount": 100, "vat_rate": 0.19}]

    with pytest.raises(VatComputationError):
        calculate_vat_payable_by_jurisdiction(transactions)
