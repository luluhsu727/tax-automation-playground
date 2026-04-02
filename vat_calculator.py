import json
import sys
from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


def to_decimal(value):
    """Convert a numeric input to Decimal safely."""
    return Decimal(str(value))


def normalize_rate(vat_rate):
    """Normalize rate to fraction (20 -> 0.2, 0.2 -> 0.2)."""
    rate = to_decimal(vat_rate)
    if rate > 1:
        rate = rate / Decimal("100")
    return rate


def quantize_money(value):
    """Round to cents with financial half-up rules."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def transaction_vat(txn):
    """Compute VAT amount for a single transaction."""
    if "vat_amount" in txn and txn["vat_amount"] is not None:
        return quantize_money(to_decimal(txn["vat_amount"]))

    if "amount" not in txn or "vat_rate" not in txn:
        raise ValueError(
            "Each transaction must contain either vat_amount, or amount and vat_rate."
        )

    amount = to_decimal(txn["amount"])
    rate = normalize_rate(txn["vat_rate"])
    return quantize_money(amount * rate)


def calculate_vat_by_jurisdiction(transactions):
    """
    Compute VAT payable/refundable per jurisdiction.

    Returns a dictionary keyed by jurisdiction:
      {
        "FR": {
          "output_vat": 20.00,
          "input_vat": 6.00,
          "net_vat": 14.00,
          "vat_payable": 14.00,
          "vat_refundable": 0.00
        }
      }
    """
    summary = {}

    for txn in transactions:
        if "jurisdiction" not in txn:
            raise ValueError("Each transaction must include a jurisdiction.")
        if "type" not in txn:
            raise ValueError("Each transaction must include a type (sale/purchase).")

        jurisdiction = txn["jurisdiction"]
        txn_type = txn["type"]
        vat_amount = transaction_vat(txn)

        if jurisdiction not in summary:
            summary[jurisdiction] = {
                "output_vat": Decimal("0.00"),
                "input_vat": Decimal("0.00"),
            }

        if txn_type == "sale":
            summary[jurisdiction]["output_vat"] += vat_amount
        elif txn_type == "purchase":
            summary[jurisdiction]["input_vat"] += vat_amount
        else:
            raise ValueError("Transaction type must be either 'sale' or 'purchase'.")

    for values in summary.values():
        values["output_vat"] = quantize_money(values["output_vat"])
        values["input_vat"] = quantize_money(values["input_vat"])
        net = quantize_money(values["output_vat"] - values["input_vat"])
        values["net_vat"] = net
        values["vat_payable"] = net if net > 0 else Decimal("0.00")
        values["vat_refundable"] = -net if net < 0 else Decimal("0.00")

    return summary


def calculate_vat_payable_by_jurisdiction(transactions):
    """Backward-compatible alias focused on payable wording."""
    return calculate_vat_by_jurisdiction(transactions)


def serialize_summary(summary):
    """Convert Decimal fields to float for JSON output."""
    result = {}
    for jurisdiction, values in summary.items():
        result[jurisdiction] = {
            key: float(quantize_money(value)) for key, value in values.items()
        }
    return result


def main(argv):
    if len(argv) != 2:
        print("Usage: python vat_calculator.py <transactions.json>")
        return 1

    path = argv[1]
    with open(path, "r", encoding="utf-8") as f:
        transactions = json.load(f)

    summary = calculate_vat_by_jurisdiction(transactions)
    print(json.dumps(serialize_summary(summary), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
