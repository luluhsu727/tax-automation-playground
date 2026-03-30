from vat_payable import (
    VatComputationError,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_to_be_paid_for_each_jurisdiction,
    vat_payable_by_jurisdiction,
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


def test_accepts_taxable_amount_and_country_aliases():
    transactions = [
        {"country": "de", "taxable_amount": "100.00", "vat_rate": "19"},
        {"country": "DE", "taxable_amount": "50.00", "vat_rate": "0.19"},
        {"country": "fr", "revenue": "80.00", "vat_rate": "0.20"},
    ]

    result = vat_payable_by_jurisdiction(transactions)
    assert result == {"DE": 28.5, "FR": 16.0}


def test_rejects_invalid_transaction_type():
    transactions = [
        {"jurisdiction": "DE", "type": "refund", "amount": 100, "vat_rate": 0.19},
    ]

    try:
        calculate_vat_payable_by_jurisdiction(transactions)
        assert False, "Expected VatComputationError"
    except VatComputationError as exc:
        assert "Unsupported transaction type" in str(exc)


def test_uses_default_rate_when_vat_rate_missing():
    transactions = [
        {"jurisdiction": "DE", "amount": 100},
        {"jurisdiction": "DE", "amount": 50},
        {"jurisdiction": "FR", "amount": 80},
    ]
    result = generate_vat_to_be_paid_for_each_jurisdiction(transactions)
    assert result == {"DE": 28.5, "FR": 16.0}


def test_rejects_missing_default_rate_when_vat_rate_missing():
    transactions = [{"jurisdiction": "NL", "amount": 100}]
    try:
        vat_payable_by_jurisdiction(transactions)
        assert False, "Expected VatComputationError"
    except VatComputationError as exc:
        assert "No VAT rate supplied for jurisdiction 'NL'" in str(exc)
