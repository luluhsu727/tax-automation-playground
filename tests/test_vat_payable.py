from decimal import Decimal

from vat.payable import VATRecord, calculate_vat_payable_by_jurisdiction


def test_calculates_net_vat_payable_per_jurisdiction() -> None:
    records = [
        VATRecord(jurisdiction="DE", output_vat=Decimal("120.00"), input_vat=Decimal("20.00")),
        VATRecord(jurisdiction="DE", output_vat=Decimal("80.00"), input_vat=Decimal("5.00")),
        VATRecord(jurisdiction="FR", output_vat=Decimal("50.00"), input_vat=Decimal("65.00")),
    ]

    result = calculate_vat_payable_by_jurisdiction(records)

    assert result == {
        "DE": Decimal("175.00"),
        "FR": Decimal("-15.00"),
    }


def test_accepts_mapping_records_and_rounds_to_cents() -> None:
    records = [
        {"jurisdiction": "UK", "output_vat": "10.005", "input_vat": "0"},
        {"jurisdiction": "UK", "output_vat": 0, "input_vat": "2.001"},
        {"jurisdiction": "ES", "output_vat": "8.4", "input_vat": "3.2"},
    ]

    result = calculate_vat_payable_by_jurisdiction(records)

    assert result == {
        "UK": Decimal("8.01"),
        "ES": Decimal("5.20"),
    }


def test_can_clamp_negative_payables_to_zero() -> None:
    records = [
        VATRecord(jurisdiction="FR", output_vat=Decimal("10"), input_vat=Decimal("30")),
    ]

    result = calculate_vat_payable_by_jurisdiction(records, clamp_negative=True)

    assert result == {"FR": Decimal("0.00")}


def test_rejects_invalid_jurisdiction() -> None:
    try:
        calculate_vat_payable_by_jurisdiction([{"jurisdiction": " ", "output_vat": 1, "input_vat": 0}])
    except ValueError as exc:
        assert "jurisdiction" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty jurisdiction")


def test_rejects_invalid_amounts() -> None:
    try:
        calculate_vat_payable_by_jurisdiction([{"jurisdiction": "DE", "output_vat": "x", "input_vat": 0}])
    except ValueError as exc:
        assert "Invalid VAT amount" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid VAT amount")
