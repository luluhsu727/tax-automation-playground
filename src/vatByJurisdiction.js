"use strict";

const SUPPORTED_DIRECTIONS = new Set(["sale", "purchase", "output", "input"]);

/**
 * Generate VAT payable totals grouped by jurisdiction.
 *
 * @param {Array<{
 *   jurisdiction: string,
 *   direction: "sale" | "purchase" | "output" | "input",
 *   vatAmount?: number,
 *   amount?: number,
 *   vatRate?: number
 * }>} transactions
 * @returns {Array<{
 *   jurisdiction: string,
 *   outputVat: number,
 *   inputVat: number,
 *   vatPayable: number
 * }>}
 */
function calculateVatPayableByJurisdiction(transactions) {
  if (!Array.isArray(transactions)) {
    throw new TypeError("transactions must be an array");
  }

  const aggregate = new Map();

  for (const transaction of transactions) {
    if (!transaction || typeof transaction !== "object") {
      throw new TypeError("each transaction must be an object");
    }

    validateJurisdiction(transaction.jurisdiction);
    const jurisdiction = transaction.jurisdiction.trim();
    const direction = normalizeDirection(transaction.direction);
    const vatAmount = getVatAmount(transaction);

    const bucket = aggregate.get(jurisdiction) ?? { outputVat: 0, inputVat: 0 };
    if (direction === "sale") {
      bucket.outputVat += vatAmount;
    } else {
      bucket.inputVat += vatAmount;
    }

    aggregate.set(jurisdiction, bucket);
  }

  return Array.from(aggregate.entries())
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([jurisdiction, totals]) => ({
      jurisdiction,
      outputVat: roundCurrency(totals.outputVat),
      inputVat: roundCurrency(totals.inputVat),
      vatPayable: roundCurrency(totals.outputVat - totals.inputVat),
    }));
}

function validateJurisdiction(jurisdiction) {
  if (typeof jurisdiction !== "string" || jurisdiction.trim().length === 0) {
    throw new Error("jurisdiction is required and must be a non-empty string");
  }
}

function normalizeDirection(direction) {
  if (typeof direction !== "string") {
    throw new TypeError("direction must be a string");
  }

  const normalized = direction.toLowerCase();
  if (!SUPPORTED_DIRECTIONS.has(normalized)) {
    throw new Error(
      `Unsupported direction "${direction}". Use one of: ${Array.from(SUPPORTED_DIRECTIONS).join(", ")}`
    );
  }

  return normalized === "output" ? "sale" : normalized === "input" ? "purchase" : normalized;
}

function getVatAmount(transaction) {
  if (transaction.vatAmount != null) {
    return toFiniteNumber(transaction.vatAmount, "vatAmount");
  }

  const amount = toFiniteNumber(transaction.amount, "amount");
  if (amount < 0) {
    throw new RangeError(`amount cannot be negative. Received: ${amount}`);
  }

  return amount * toNormalizedRate(transaction.vatRate);
}

function toNormalizedRate(rawRate) {
  if (rawRate == null) {
    return 0;
  }

  const rate = toFiniteNumber(rawRate, "vatRate");
  if (rate < 0) {
    throw new RangeError(`vatRate cannot be negative. Received: ${rate}`);
  }

  // Accept both decimal rates (0.2) and percentage rates (20).
  return rate > 1 ? rate / 100 : rate;
}

function toFiniteNumber(value, fieldName) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${fieldName} must be a finite number`);
  }

  return value;
}

function roundCurrency(value) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

module.exports = {
  calculateVatPayableByJurisdiction,
  toNormalizedRate,
};
