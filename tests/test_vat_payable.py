from decimal import Decimal

import pytest

from tax_engine import Transaction, calculate_vat_payable_by_jurisdiction
from vat_payable import load_transactions


def test_calculate_vat_payable_by_jurisdiction_mixed_transactions() -> None:
    transactions = [
        Transaction("DE", "sale", Decimal("1000"), vat_rate=Decimal("0.19")),
        Transaction("DE", "purchase", Decimal("400"), vat_rate=Decimal("0.19")),
        Transaction("FR", "sale", Decimal("500"), vat_rate=Decimal("0.20")),
        Transaction("FR", "purchase", Decimal("700"), vat_rate=Decimal("0.20")),
        Transaction("IT", "sale", Decimal("1000"), vat_amount=Decimal("220")),
        Transaction("IT", "purchase", Decimal("200"), vat_amount=Decimal("44")),
    ]

    result = calculate_vat_payable_by_jurisdiction(transactions)

    assert result == {
        "DE": Decimal("114.00"),
        "FR": Decimal("-40.00"),
        "IT": Decimal("176.00"),
    }


def test_load_transactions_requires_mandatory_columns(tmp_path) -> None:
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("country,kind,amount\nDE,sale,1000\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Input CSV must include columns"):
        load_transactions(bad_csv)

