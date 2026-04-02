from vat_payable import (
    calculate_vat_payable_by_jurisdiction,
    compute_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
)


def test_calculates_vat_payable_for_multiple_jurisdictions():
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
        {"jurisdiction": "DE", "type": "purchase", "amount": 250, "vat_rate": 0.19},
        {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.20},
        {"jurisdiction": "FR", "type": "purchase", "amount": 100, "vat_rate": 0.20},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {
        "DE": {"output_vat": 190.0, "input_vat": 47.5, "vat_payable": 142.5},
        "FR": {"output_vat": 100.0, "input_vat": 20.0, "vat_payable": 80.0},
    }


def test_rounds_currency_values_to_two_decimal_places():
    transactions = [
        {"jurisdiction": "ES", "type": "sale", "amount": 10.01, "vat_rate": 0.21},
        {"jurisdiction": "ES", "type": "purchase", "amount": 3.33, "vat_rate": 0.21},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["ES"]["output_vat"] == 2.1
    assert result["ES"]["input_vat"] == 0.7
    assert result["ES"]["vat_payable"] == 1.4


def test_rejects_invalid_transaction_type():
    transactions = [
        {"jurisdiction": "DE", "type": "refund", "amount": 100, "vat_rate": 0.19},
    ]

    try:
        calculate_vat_payable_by_jurisdiction(transactions)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported transaction type" in str(exc)


def test_rejects_negative_amount():
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "amount": -1, "vat_rate": 0.19},
    ]

    try:
        calculate_vat_payable_by_jurisdiction(transactions)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Amount cannot be negative" in str(exc)


def test_accepts_percentage_style_vat_rate_inputs():
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "amount": 100, "vat_rate": 19},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)
    assert result["DE"]["vat_payable"] == 19.0


def test_generate_vat_to_be_paid_for_sales_purchase_schema():
    transactions = [
        {"jurisdiction": "DE", "type": "sale", "amount": 1000, "vat_rate": 0.19},
        {"jurisdiction": "DE", "type": "purchase", "amount": 250, "vat_rate": 0.19},
    ]

    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
    assert result == {"DE": 142.5}


def test_compute_alias_matches_calculate_function():
    transactions = [
        {"jurisdiction": "FR", "type": "sale", "amount": 500, "vat_rate": 0.2},
    ]

    assert compute_vat_payable_by_jurisdiction(
        transactions
    ) == calculate_vat_payable_by_jurisdiction(transactions)
