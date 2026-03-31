const test = require("node:test");
const assert = require("node:assert/strict");

const { calculateVatPayableByJurisdiction } = require("../src/vatByJurisdiction");

test("calculates VAT payable grouped by jurisdiction", () => {
  const transactions = [
    { jurisdiction: "DE", direction: "sale", amount: 1000, vatRate: 0.19 },
    { jurisdiction: "DE", direction: "purchase", amount: 250, vatRate: 0.19 },
    { jurisdiction: "FR", direction: "sale", amount: 500, vatRate: 0.2 },
    { jurisdiction: "FR", direction: "purchase", amount: 100, vatRate: 0.2 }
  ];

  assert.deepEqual(calculateVatPayableByJurisdiction(transactions), [
    { jurisdiction: "DE", outputVat: 190, inputVat: 47.5, vatPayable: 142.5 },
    { jurisdiction: "FR", outputVat: 100, inputVat: 20, vatPayable: 80 }
  ]);
});

test("accepts explicit VAT amount when provided", () => {
  const transactions = [
    { jurisdiction: "ES", direction: "sale", vatAmount: 30 },
    { jurisdiction: "ES", direction: "purchase", vatAmount: 5.25 }
  ];

  assert.deepEqual(calculateVatPayableByJurisdiction(transactions), [
    { jurisdiction: "ES", outputVat: 30, inputVat: 5.25, vatPayable: 24.75 }
  ]);
});

test("accepts percentage VAT rates", () => {
  const transactions = [{ jurisdiction: "IT", direction: "sale", amount: 100, vatRate: 22 }];

  assert.deepEqual(calculateVatPayableByJurisdiction(transactions), [
    { jurisdiction: "IT", outputVat: 22, inputVat: 0, vatPayable: 22 }
  ]);
});

test("throws on invalid direction", () => {
  const transactions = [{ jurisdiction: "DE", direction: "refund", amount: 100, vatRate: 0.19 }];

  assert.throws(
    () => calculateVatPayableByJurisdiction(transactions),
    /Unsupported direction/
  );
});

test("throws when jurisdiction is missing", () => {
  const transactions = [{ direction: "sale", amount: 100, vatRate: 0.19 }];

  assert.throws(
    () => calculateVatPayableByJurisdiction(transactions),
    /jurisdiction is required/
  );
});
