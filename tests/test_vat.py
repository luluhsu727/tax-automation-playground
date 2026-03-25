from decimal import Decimal

import pytest

from tax_automation.vat import (
    VATTransaction,
    calculate_vat_payable_by_jurisdiction,
    load_transactions_from_csv,
    summarize_vat_by_jurisdiction,
)


def test_summarize_vat_by_jurisdiction_computes_payable() -> None:
    transactions = [
        VATTransaction(
            jurisdiction="DE",
            transaction_type="sale",
            net_amount=Decimal("100.00"),
            vat_rate=Decimal("0.19"),
        ),
        VATTransaction(
            jurisdiction="DE",
            transaction_type="purchase",
            net_amount=Decimal("20.00"),
            vat_rate=Decimal("0.19"),
        ),
        VATTransaction(
            jurisdiction="FR",
            transaction_type="sale",
            net_amount=Decimal("50.00"),
            vat_rate=Decimal("0.20"),
        ),
    ]

    summary = summarize_vat_by_jurisdiction(transactions)

    assert summary["DE"].output_vat == Decimal("19.00")
    assert summary["DE"].input_vat == Decimal("3.80")
    assert summary["DE"].vat_payable == Decimal("15.20")
    assert summary["DE"].transaction_count == 2

    assert summary["FR"].output_vat == Decimal("10.00")
    assert summary["FR"].input_vat == Decimal("0.00")
    assert summary["FR"].vat_payable == Decimal("10.00")
    assert summary["FR"].transaction_count == 1


def test_calculate_vat_payable_by_jurisdiction_returns_only_payable() -> None:
    transactions = [
        VATTransaction(
            jurisdiction="NL",
            transaction_type="sale",
            net_amount=Decimal("200"),
            vat_rate=Decimal("0.21"),
        ),
        VATTransaction(
            jurisdiction="NL",
            transaction_type="purchase",
            net_amount=Decimal("100"),
            vat_rate=Decimal("0.21"),
        ),
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {"NL": Decimal("21.00")}


def test_invalid_transaction_type_is_rejected() -> None:
    transactions = [
        VATTransaction(
            jurisdiction="ES",
            transaction_type="refund",
            net_amount=Decimal("100"),
            vat_rate=Decimal("0.21"),
        ),
    ]

    with pytest.raises(ValueError, match="transaction_type"):
        summarize_vat_by_jurisdiction(transactions)


def test_load_transactions_from_csv_supports_optional_vat_amount(tmp_path) -> None:
    csv_path = tmp_path / "transactions.csv"
    csv_path.write_text(
        "\n".join(
            [
                "jurisdiction,transaction_type,net_amount,vat_rate,vat_amount",
                "GB,sale,100.00,0.20,",
                "GB,purchase,100.00,0.20,19.99",
            ]
        ),
        encoding="utf-8",
    )

    transactions = load_transactions_from_csv(csv_path)
    summary = summarize_vat_by_jurisdiction(transactions)

    # First row derives VAT (20.00), second row uses explicit VAT (19.99).
    assert summary["GB"].vat_payable == Decimal("0.01")
