const { calculateVatPayableByJurisdiction } = require("./vatByJurisdiction");

const sampleTransactions = [
  { id: "inv-1001", jurisdiction: "DE", direction: "sale", amount: 1000, vatRate: 0.19 },
  { id: "inv-1002", jurisdiction: "DE", direction: "purchase", amount: 400, vatRate: 0.19 },
  { id: "inv-1003", jurisdiction: "FR", direction: "sale", amount: 2000, vatRate: 20 },
  { id: "inv-1004", jurisdiction: "FR", direction: "purchase", vatAmount: 120 },
];

const report = calculateVatPayableByJurisdiction(sampleTransactions);
console.log(JSON.stringify(report, null, 2));
