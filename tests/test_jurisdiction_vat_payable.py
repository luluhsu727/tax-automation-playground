from decimal import Decimal

from jurisdiction_vat_payable import (
    compute_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


def test_compute_summary_rows():
    transactions = [
        {"jurisdiction": "DE", "taxable_amount": Decimal("100.00"), "vat_rate": None},
        {"jurisdiction": "DE", "taxable_amount": Decimal("50.00"), "vat_rate": None},
        {"jurisdiction": "FR", "taxable_amount": Decimal("80.00"), "vat_rate": None},
    ]
    summary = compute_vat_payable_by_jurisdiction(transactions)
    assert summary == [
        {
            "jurisdiction": "DE",
            "total_taxable_amount": "150.00",
            "total_vat_payable": "28.50",
            "effective_vat_rate": "0.19",
        },
        {
            "jurisdiction": "FR",
            "total_taxable_amount": "80.00",
            "total_vat_payable": "16.00",
            "effective_vat_rate": "0.20",
        },
    ]


def test_generate_vat_to_be_paid_for_each_jurisdiction():
    transactions = [
        {"jurisdiction": "ES", "taxable_amount": "100.00", "vat_rate": "0.21"},
        {"jurisdiction": "ES", "taxable_amount": "20.00", "vat_rate": "0.21"},
        {"jurisdiction": "IT", "taxable_amount": "10.00", "vat_rate": "0.22"},
    ]
    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
    assert result == {
        "ES": Decimal("25.2"),
        "IT": Decimal("2.2"),
    }
