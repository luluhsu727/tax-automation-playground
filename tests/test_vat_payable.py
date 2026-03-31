from decimal import Decimal

import pytest

from vat_payable import Transaction, vat_to_be_paid_by_jurisdiction


def test_calculates_net_vat_payable_per_jurisdiction() -> None:
    transactions = [
        Transaction(jurisdiction="DE", amount="100.00", vat_rate="0.19", kind="sale"),  # 19.00
        Transaction(jurisdiction="DE", amount="80.00", vat_rate="0.19", kind="purchase"),  # -15.20
        Transaction(jurisdiction="FR", amount="200.00", vat_rate="0.20", kind="sale"),  # 40.00
        Transaction(jurisdiction="FR", amount="10.00", vat_amount="2.00", kind="purchase"),  # -2.00
    ]

    assert vat_to_be_paid_by_jurisdiction(transactions) == {
        "DE": Decimal("3.80"),
        "FR": Decimal("38.00"),
    }


def test_accepts_dictionary_records() -> None:
    transactions = [
        {"jurisdiction": "ES", "amount": "50", "vat_rate": "0.21", "kind": "sale"},
        {"jurisdiction": "ES", "amount": "10", "vat_amount": "2.10", "kind": "purchase"},
    ]

    assert vat_to_be_paid_by_jurisdiction(transactions) == {"ES": Decimal("8.40")}


def test_raises_when_vat_info_is_missing() -> None:
    transactions = [{"jurisdiction": "US", "amount": "100", "kind": "sale"}]
    with pytest.raises(ValueError, match="vat_amount or vat_rate"):
        vat_to_be_paid_by_jurisdiction(transactions)


def test_raises_on_unknown_transaction_kind() -> None:
    transactions = [{"jurisdiction": "DE", "amount": "100", "vat_rate": "0.19", "kind": "refund"}]
    with pytest.raises(ValueError, match="must be either 'sale' or 'purchase'"):
        vat_to_be_paid_by_jurisdiction(transactions)
