# The Solver Race — Challenge Description & Organizer Overview

## Challenge Metadata

- **Name**: The Solver Race
- **Category**: Web / Fintech Systems
- **Difficulty**: 300 Points / Hard (College / University Level CTF)
- **Flag Format**: `CHAKRAVYUHA{...}`
- **Flag**: `CHAKRAVYUHA{x_l4y3r_st4t3_1d3nt1ty_r3c0nc1l3_8f19}`
- **Target Solve Time**: 45–90 minutes for a strong undergraduate web CTF player
- **AI-Resistance Rating**: 9/10

---

## Public CTF Scoreboard Description (Given to Player)

```markdown
# The Solver Race

**Category**: Web / Fintech Systems  
**Points**: 300 Points  
**Difficulty**: Hard  
**Flag Format**: `CHAKRAVYUHA{...}`  

The settlement network is running its final supervisory reconciliation round.

Your solver account has been provisioned with access to the clearinghouse operations console and allocated a dedicated channel reserve backed by institutional liquidity.

Complete the assigned settlement workflow and obtain the final supervisory reconciliation certificate.

The clearinghouse exposes the standard HTTP interfaces used by all competing algorithmic market solvers.

**Target**: The challenge instance provided by the organizers.
```

---

## Educational Concepts & Intended Vulnerability

1. **Multi-Subsystem Object Identity Inconsistency**:
   - `QuoteService`: Identifies the trade by logical `quote_id` (`QTE-XXXX`).
   - `SettlementService`: Enforces execution uniqueness on the specific quote revision reference: `quote_ref` (`QTE-XXXX:r1`, `QTE-XXXX:r2`).
   - `ReceiptService`: Enforces clearance finality on the logical root quote ID (`quote_id`). Once a receipt is sealed, the quote is marked permanently `ARCHIVED`.
   - `LedgerService`: Aggregates double-entry journals and debits the channel's finite reserve pool for every posted settlement.

2. **Accounting Solvency Invariant**:
   - Initial Reserve: 1500.00 CR
   - Statutory Solvency Floor: 500.00 CR
   - Honest settlement across all 3 market orders clears ~810 CR, leaving ~690 CR in the reserve, which remains `COMPLIANT`.
   - By repeatedly adjusting unsealed quotes to create fresh revisions (`r2`, `r3`, ...) and settling each revision, the reserve is driven into a `CRITICAL_DEFICIT` state (< 500.00 CR).

3. **Supervisory Reconciliation Trigger**:
   - Calling `POST /api/reconciliation/audit` after breaching the solvency floor triggers the statutory emergency intervention protocol.
   - The reconciliation engine generates an official emergency resolution certificate containing the flag in the `attestation_seal` field.
