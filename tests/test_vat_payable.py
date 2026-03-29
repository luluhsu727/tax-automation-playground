from vat_payable import calculate_vat_payable_by_jurisdiction


def test_calculate_with_explicit_vat_fields():
    transactions = [
        {"jurisdiction": "DE", "output_vat": 100, "input_vat": 20},
        {"jurisdiction": "DE", "output_vat": 50, "input_vat": 10},
        {"jurisdiction": "FR", "output_vat": 80, "input_vat": 120},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {
        "DE": {"output_vat": 150.0, "input_vat": 30.0, "vat_payable": 120.0},
        "FR": {"output_vat": 80.0, "input_vat": 120.0, "vat_payable": -40.0},
    }


def test_calculate_with_amount_and_rate_fields():
    transactions = [
        {"jurisdiction": "UK", "transaction_type": "sale", "amount": 1000, "vat_rate": 0.2},
        {"jurisdiction": "UK", "transaction_type": "purchase", "amount": 300, "vat_rate": 0.2},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["UK"] == {"output_vat": 200.0, "input_vat": 60.0, "vat_payable": 140.0}


def test_can_clamp_negative_vat_payable_to_zero():
    transactions = [
        {"jurisdiction": "FR", "output_vat": 40, "input_vat": 100},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions, clamp_negative_to_zero=True)

    assert result["FR"] == {"output_vat": 40.0, "input_vat": 100.0, "vat_payable": 0.0}


def test_rejects_missing_jurisdiction():
    transactions = [{"output_vat": 10, "input_vat": 2}]

    try:
        calculate_vat_payable_by_jurisdiction(transactions)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "jurisdiction" in str(exc)
