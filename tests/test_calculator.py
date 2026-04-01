from vat_payable.calculator import (
    Transaction,
    VatComputationError,
    calculate_vat_payable_by_jurisdiction,
)


def test_calculates_payable_per_jurisdiction() -> None:
    transactions = [
        Transaction(jurisdiction="DE", amount=1000, vat_rate=0.19, transaction_type="sale"),
        Transaction(jurisdiction="DE", amount=200, vat_rate=0.19, transaction_type="purchase"),
        Transaction(jurisdiction="FR", amount=500, vat_rate=0.20, transaction_type="sale"),
        Transaction(jurisdiction="FR", amount=300, vat_rate=0.20, transaction_type="purchase"),
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["DE"]["output_vat"] == 190.0
    assert result["DE"]["input_vat"] == 38.0
    assert result["DE"]["vat_payable"] == 152.0

    assert result["FR"]["output_vat"] == 100.0
    assert result["FR"]["input_vat"] == 60.0
    assert result["FR"]["vat_payable"] == 40.0


def test_supports_explicit_vat_amount() -> None:
    transactions = [
        Transaction(
            jurisdiction="ES",
            amount=1000,
            vat_rate=0.21,
            transaction_type="sale",
            vat_amount=150,
        )
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)
    assert result["ES"]["output_vat"] == 150.0
    assert result["ES"]["vat_payable"] == 150.0


def test_supports_percentage_vat_rate() -> None:
    transactions = [
        Transaction(jurisdiction="IT", amount=100, vat_rate=22, transaction_type="sale")
    ]
    result = calculate_vat_payable_by_jurisdiction(transactions)
    assert result["IT"]["output_vat"] == 22.0


def test_raises_for_invalid_transaction_type() -> None:
    transactions = [
        Transaction(jurisdiction="DE", amount=100, vat_rate=0.19, transaction_type="refund")
    ]

    try:
        calculate_vat_payable_by_jurisdiction(transactions)
        assert False, "Expected VatComputationError to be raised"
    except VatComputationError as exc:
        assert "Unsupported transaction_type" in str(exc)
