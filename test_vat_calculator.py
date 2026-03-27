from decimal import Decimal

from vat_calculator import Transaction, calculate_vat_payable_by_jurisdiction


def test_calculates_net_vat_payable_per_jurisdiction() -> None:
    transactions = [
        Transaction("DE", Decimal("1000"), Decimal("19"), "sale"),      # 190.00 output
        Transaction("DE", Decimal("200"), Decimal("19"), "purchase"),   # 38.00 input
        Transaction("FR", Decimal("300"), Decimal("20"), "sale"),       # 60.00 output
        Transaction("FR", Decimal("100"), Decimal("20"), "purchase"),   # 20.00 input
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {
        "DE": Decimal("152.00"),
        "FR": Decimal("40.00"),
    }


def test_handles_fractional_rates_and_refund_positions() -> None:
    transactions = [
        Transaction("UK", Decimal("100"), Decimal("0.2"), "sale"),        # 20.00 output
        Transaction("UK", Decimal("200"), Decimal("0.2"), "purchase"),    # 40.00 input
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result["UK"] == Decimal("-20.00")


def test_rejects_negative_rate() -> None:
    transactions = [
        Transaction("DE", Decimal("100"), Decimal("-1"), "sale"),
    ]

    try:
        calculate_vat_payable_by_jurisdiction(transactions)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "vat_rate cannot be negative" in str(exc)
