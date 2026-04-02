from decimal import Decimal

import pytest

from jurisdiction_vat_payable import (
    compute_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


def test_compute_vat_payable_with_provided_rates():
    transactions = [
        {"jurisdiction": "DE", "taxable_amount": "100.00", "vat_rate": "0.19"},
        {"jurisdiction": "DE", "taxable_amount": "50.00", "vat_rate": "0.19"},
        {"jurisdiction": "FR", "taxable_amount": "200.00", "vat_rate": "0.20"},
    ]

    result = compute_vat_payable_by_jurisdiction(transactions)

    assert result == [
        {
            "jurisdiction": "DE",
            "total_taxable_amount": "150.00",
            "total_vat_payable": "28.50",
            "effective_vat_rate": "0.19",
        },
        {
            "jurisdiction": "FR",
            "total_taxable_amount": "200.00",
            "total_vat_payable": "40.00",
            "effective_vat_rate": "0.20",
        },
    ]


def test_generate_vat_payable_uses_default_rate_when_missing():
    transactions = [
        {"jurisdiction": "DE", "taxable_amount": Decimal("100.00")},
        {"jurisdiction": "FR", "taxable_amount": Decimal("200.00")},
    ]

    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)

    assert result == {"DE": Decimal("19.00"), "FR": Decimal("40.00")}


def test_supports_percentage_rates():
    transactions = [{"jurisdiction": "IT", "taxable_amount": "100.00", "vat_rate": "22"}]

    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)

    assert result == {"IT": Decimal("22.00")}


def test_raises_on_missing_default_and_missing_rate():
    transactions = [{"jurisdiction": "NL", "taxable_amount": "100.00"}]

    with pytest.raises(ValueError, match="No VAT rate supplied for jurisdiction 'NL'"):
        generate_vat_to_be_paid_for_each_jurisdiction(transactions)
