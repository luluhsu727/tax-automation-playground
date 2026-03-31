# tax-automation-playground

Generate VAT to be paid for each jurisdiction.

## Install

```bash
npm install
```

## Run the sample report

```bash
npm run vat:report
```

This prints an array where each item has:

- `jurisdiction`
- `outputVat`
- `inputVat`
- `vatPayable` (`outputVat - inputVat`)

## Transaction shape

`calculateVatPayableByJurisdiction(transactions)` expects an array of objects:

- `jurisdiction` (string, required)
- `direction` (string, required): one of `sale`, `purchase`, `output`, `input`
- `vatAmount` (number, optional)
- `amount` (number, required when `vatAmount` is not provided)
- `vatRate` (number, optional when `vatAmount` is provided; accepts decimal rates like `0.2` or percent-like rates like `20`)

## Run tests

```bash
npm test
```
