from vat_calculator import compute_vat_to_be_paid


def test_compute_vat_to_be_paid_multiple_jurisdictions():
    transactions = [
        {"jurisdiction": "DE", "amount": 1000, "vat_rate": "19%", "transaction_type": "sale"},
        {"jurisdiction": "DE", "amount": 200, "vat_rate": 0.19, "transaction_type": "purchase"},
        {"jurisdiction": "FR", "amount": 500, "vat_rate": "20%", "transaction_type": "sale"},
        {"jurisdiction": "FR", "vat_amount": "30.25", "transaction_type": "purchase"},
    ]

    result = compute_vat_to_be_paid(transactions)

    assert result == {
        "DE": 152.0,   # 190 - 38
        "FR": 69.75,   # 100 - 30.25
    }


def test_compute_vat_to_be_paid_allows_negative_balance():
    transactions = [
        {"jurisdiction": "ES", "amount": 100, "vat_rate": "21%", "transaction_type": "sale"},
        {"jurisdiction": "ES", "amount": 300, "vat_rate": "21%", "transaction_type": "purchase"},
    ]

    result = compute_vat_to_be_paid(transactions)
    assert result == {"ES": -42.0}


def test_compute_vat_to_be_paid_rejects_invalid_transaction_type():
    transactions = [
        {"jurisdiction": "IT", "amount": 100, "vat_rate": "22%", "transaction_type": "refund"}
    ]

    try:
        compute_vat_to_be_paid(transactions)
        assert False, "Expected ValueError for invalid transaction type."
    except ValueError as exc:
        assert "Invalid transaction_type" in str(exc)

