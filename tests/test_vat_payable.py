from decimal import Decimal

import pytest

from src.vat_payable import (
    Transaction,
    calculate_vat_payable_by_jurisdiction,
    generate_vat_payable_report,
    main,
)


def test_calculates_vat_payable_grouped_by_jurisdiction() -> None:
    transactions = [
        {"jurisdiction": "DE", "net_amount": "100.00", "vat_rate": "0.19", "transaction_type": "sale"},
        {"jurisdiction": "DE", "net_amount": "50.00", "vat_rate": "0.19", "transaction_type": "purchase"},
        {"jurisdiction": "FR", "net_amount": "200.00", "vat_rate": "0.20", "transaction_type": "sale"},
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {"DE": Decimal("9.50"), "FR": Decimal("40.00")}


def test_supports_transaction_objects() -> None:
    transactions = [
        Transaction("UK", Decimal("120"), Decimal("0.20"), "sale"),
        Transaction("UK", Decimal("20"), Decimal("0.20"), "purchase"),
    ]

    result = generate_vat_payable_report(transactions)

    assert result == {"UK": "20.00"}


@pytest.mark.parametrize(
    "bad_transaction,expected_substring",
    [
        (
            {"jurisdiction": "ES", "net_amount": "100", "vat_rate": "0.21", "transaction_type": "refund"},
            "Unsupported transaction_type",
        ),
        (
            {"jurisdiction": "ES", "net_amount": "-1", "vat_rate": "0.21", "transaction_type": "sale"},
            "net_amount must be non-negative",
        ),
        (
            {"jurisdiction": "ES", "net_amount": "100", "vat_rate": "-0.01", "transaction_type": "sale"},
            "vat_rate must be non-negative",
        ),
    ],
)
def test_validation_errors(bad_transaction: dict[str, str], expected_substring: str) -> None:
    with pytest.raises(ValueError, match=expected_substring):
        calculate_vat_payable_by_jurisdiction([bad_transaction])


def test_cli_with_stdin(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "sys.stdin",
        __import__("io").StringIO(
            '[{"jurisdiction":"DE","net_amount":"100","vat_rate":"0.19","transaction_type":"sale"}]'
        ),
    )

    exit_code = main(["--input", "-"])
    out = capsys.readouterr().out.strip()

    assert exit_code == 0
    assert out == '{"DE":"19.00"}'


def test_cli_errors_are_non_zero(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO('{"not":"a-list"}'))

    exit_code = main(["--input", "-"])
    err = capsys.readouterr().err

    assert exit_code == 1
    assert "Input JSON must be a list" in err
