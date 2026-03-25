from decimal import Decimal

import pytest

from jurisdiction_vat_payable import (
    compute_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    load_transactions,
)


def test_compute_summary_with_default_rates() -> None:
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


def test_generate_vat_to_be_paid_for_each_jurisdiction() -> None:
    transactions = [
        {"jurisdiction": "ES", "taxable_amount": "100.00", "vat_rate": "0.21"},
        {"jurisdiction": "ES", "taxable_amount": "20.00", "vat_rate": "0.21"},
        {"jurisdiction": "IT", "taxable_amount": "10.00", "vat_rate": "0.22"},
    ]

    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
    assert result == {
        "ES": Decimal("25.20"),
        "IT": Decimal("2.20"),
    }


def test_load_transactions_accepts_country_and_revenue(tmp_path) -> None:
    input_csv = tmp_path / "input.csv"
    input_csv.write_text(
        "country,revenue\n"
        "de,100.00\n"
        "fr,50.00\n",
        encoding="utf-8",
    )

    loaded = load_transactions(input_csv)

    assert loaded == [
        {"jurisdiction": "DE", "taxable_amount": Decimal("100.00"), "vat_rate": None},
        {"jurisdiction": "FR", "taxable_amount": Decimal("50.00"), "vat_rate": None},
    ]


def test_missing_default_rate_raises_error() -> None:
    transactions = [
        {"jurisdiction": "NL", "taxable_amount": Decimal("100.00"), "vat_rate": None},
    ]

    with pytest.raises(ValueError, match="No VAT rate supplied for jurisdiction 'NL'"):
        compute_vat_payable_by_jurisdiction(transactions)
