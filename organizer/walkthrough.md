# Organizer Walkthrough: The Solver Race

## Challenge Overview

- **Title**: The Solver Race
- **Category**: Web / Fintech Systems
- **Difficulty**: 300 Points / Hard
- **Estimated Solve Time**: 45–90 minutes
- **Flag**: `CHAKRAVYUHA{x_l4y3r_st4t3_1d3nt1ty_r3c0nc1l3_8f19}`

---

## Detailed Step-by-Step Analysis & Discovery Path

### Step 1: Normal Application Enumeration
A competitor begins by probing the application:
1. Navigating to `http://localhost:8000/` reveals a financial operations console ("The Solver Race").
2. Creating an account via `POST /api/account/register` returns a bearer token, a solver account identifier (`SLV-XXXX`), and reveals two key metrics:
   - `reserve_balance`: 1500.00 CR
   - `solvency_floor`: 500.00 CR
3. Inspecting `GET /api/orders` reveals three institutional settlement demands:
   - `ORD-801` (nominal 1000.0, base rate 1.05, target fee 180 bps)
   - `ORD-802` (nominal 1400.0, base rate 1.02, target fee 160 bps)
   - `ORD-803` (nominal 1800.0, base rate 1.08, target fee 200 bps)
4. Inspecting `GET /api/reconciliation/status` reveals the supervisory compliance telemetry:
   - Initial reserve: 1500.00 CR
   - Statutory floor: 500.00 CR
   - Current status: `COMPLIANT`
5. Calling `POST /api/reconciliation/audit` early yields a standard operational certificate (`STANDARD_SUPERVISORY_CLEARANCE`) with no flag.

---

### Step 2: Understanding the Quote Lifecycle
When a solver submits a quote via `POST /api/quotes`:
```json
{
  "order_id": "ORD-801",
  "rate": 1.05,
  "spread_bps": 180,
  "allocation_pct": 100.0
}
```
The response reveals two distinct identifier tiers:
- `quote_id`: `QTE-4A05A3` (the logical business entity)
- `quote_ref`: `QTE-4A05A3:r1` (the specific revision reference)
- `current_revision`: 1
- `state`: `ACTIVE`
- `signature`: cryptographic commitment hash of `(quote_ref, order_id, rate, payout_amount)`

The calculated payout amount for `ORD-801` is:
$$1000.0 \times 1.05 \times \frac{180}{1000.0} = 189.00 \text{ CR}$$

---

### Step 3: Comparing Quote Revisions
The application provides an adjustment endpoint:
`POST /api/quotes/{id}/adjust` with `{"rate_delta": 0.01, "spread_delta": 30}`.

Invoking this endpoint updates the terms:
- `quote_id` remains constant (`QTE-4A05A3`).
- `current_revision` increments to 2.
- A new revision ticket is generated: `quote_ref = "QTE-4A05A3:r2"`.
- A new payout is calculated (e.g. 222.60 CR).
- Both revisions exist in the quote history returned by `GET /api/quotes/{id}`.

---

### Step 4: Comparing Settlement Requests & Responses
To settle, the solver sends:
```http
POST /api/settlements
Content-Type: application/json
Authorization: Bearer <token>

{
  "quote_ref": "QTE-4A05A3:r1"
}
```
The settlement succeeds:
- `settlement_id`: `STL-XXXX`
- `settlement_identity`: `hash(account_id, order_id, "QTE-4A05A3:r1")`
- Ledger records a double-entry debit of 189.00 CR to `RESERVE_POOL` and credits the solver account.
- `reserve_balance` drops to 1311.00 CR.

**Crucial Observation (Test B)**:
If the player immediately replays `POST /api/settlements` with `QTE-4A05A3:r1`:
The clearinghouse rejects it with `409 Conflict: ERR_DUPLICATE_SETTLEMENT: Settlement operation already committed for quote reference 'QTE-4A05A3:r1'`.

---

### Step 5: Identifying the Multiple Identity Representations
Tracing the responses reveals how different subsystems track identity:
1. **Quote Subsystem**:
   - Identifies the business entity by `quote_id` (`QTE-4A05A3`).
   - Revisions are tracked by `quote_ref` (`QTE-4A05A3:r1`, `QTE-4A05A3:r2`).
2. **Settlement Subsystem**:
   - Enforces execution uniqueness by `settlement_identity = hash(account_id, order_id, quote_ref)`.
   - **This check is scoped to the specific revision reference, not the root quote ID.**
3. **Receipt Subsystem**:
   - Enforces clearance finality by `receipt_identity = hash(account_id, order_id, quote_id)`.
   - **This check is bound to the root quote ID.** Issuing a receipt transitions the root quote to `ARCHIVED`. Once archived, `POST /api/quotes/{id}/adjust` is permanently rejected with `409 Conflict`.
4. **Ledger Subsystem**:
   - Aggregates by journal entry ID and debits the shared channel liquidity reserve for every posted settlement.

---

### Step 6: Determining the Accounting Invariant
The supervisory subsystem monitors:
$$\text{Channel Reserve} \ge \text{Statutory Solvency Floor } (500.00 \text{ CR})$$

Under normal honest settlement:
- Settling ORD-801: ~189.00 CR
- Settling ORD-802: ~233.00 CR
- Settling ORD-803: ~388.00 CR
- Total normal disbursement: ~810.00 CR
- Remaining reserve: $1500.00 - 810.00 = 690.00 \text{ CR} > 500.00 \text{ CR}$.
- Honest settlement alone **never breaches the solvency floor**.

---

### Step 7: Constructing the Exact State Transition Sequence
To breach the solvency floor:
1. Do **NOT** call `POST /api/receipts` (issuing a receipt seals the root quote into `ARCHIVED`, stopping revisions).
2. Exploit the gap between `SettlementService` (keyed on `quote_ref`) and `QuoteService` (allows adjustments on unarchived quotes):
   - Settle Revision 1: `quote_ref = "QTE-XXXX:r1"`
   - Adjust Quote: produces active revision `quote_ref = "QTE-XXXX:r2"`
   - Settle Revision 2: accepted because `settlement_identity` for `r2` is unique!
   - Adjust Quote: produces active revision `quote_ref = "QTE-XXXX:r3"`
   - Settle Revision 3
   - Repeat until the reserve balance drops below 500.00 CR.

---

### Step 8: Automating the Sequence
Writing a clean script to alternate:
```python
quote = create_quote("ORD-801")
settle(quote["quote_ref"])

while current_reserve >= 500.00:
    adj = adjust_quote(quote["quote_id"], rate_delta=0.01, spread_delta=30)
    res = settle(adj["quote_ref"])
    current_reserve = res["reserve_balance_after"]
```

---

### Step 9: Triggering Reconciliation
Once `current_reserve < 500.00 CR`:
Invoke:
```http
POST /api/reconciliation/audit
Authorization: Bearer <token>
```
The supervisory engine detects:
- `solvency_status`: `CRITICAL_DEFICIT`
- `deficit_quantum`: $> 0$
- Statutory solvency corridor breached!

---

### Step 10: Obtaining the Flag
The supervisory reconciliation engine issues an emergency intervention resolution certificate:
```json
{
  "certificate_id": "CERT-RES-8820",
  "type": "SUPERVISORY_INTERVENTION_RESOLUTION",
  "reserve_status": "CRITICAL_DEFICIT",
  "recorded_reserve": 213.0,
  "statutory_solvency_floor": 500.0,
  "deficit_quantum": 287.0,
  "resolution_mandate": "STATUTORY_BAIL_IN_CONTINGENCY",
  "attestation_seal": "CHAKRAVYUHA{x_l4y3r_st4t3_1d3nt1ty_r3c0nc1l3_8f19}"
}
```
The flag is recovered directly from `attestation_seal`.
