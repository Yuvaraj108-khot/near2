# Chakravyuh Sovereign Settlement Gateway

## Challenge Metadata

- **Name**: Chakravyuh Sovereign Settlement Gateway
- **Category**: Web / Fintech Protocols
- **Difficulty**: Medium (175 Points)
- **Flag Format**: `CHAKRAVYUHA{...}`
- **Flag**: `CHAKRAVYUHA{s4pt4r4th4_cl34r1ng_st4t3_d3sync_x891b}`
- **Estimated Solve Time**: 45–75 minutes
- **Target Platform**: Docker / Linux Server / Vercel Serverless

---

## Public CTF Scoreboard Description

```markdown
> The Vyūha Clearing Engine orchestrates sovereign inter-institution liquidity settlements across concentric rings of validation. Built on the Saptaratha settlement architecture, every settlement instruction submitted to the clearinghouse is cryptographically attested by the sovereign liquidity vault, strictly ordered, and committed to double-entry ledger journals.
>
> Your institution has been allocated an operational settlement channel backed by pooled sovereign liquidity reserves. Clear funds through the concentric rings, monitor reserve adequacy against statutory requirements, and maintain institutional compliance with clearinghouse supervisory oversight.
```

---

## Summary of Educational Concepts

1. **State Machine Invariant Reasoning**:
   Real-world enterprise clearinghouses and decentralized settlement protocols claim that every transaction is processed "exactly once". However, this guarantee often relies on assumptions between disparate subsystems (ingestion buffer vs. ledger journal vs. batch closure).

2. **Cross-Layer State Desynchronization**:
   - The Intake API enforces deduplication only within the **current active batch cycle** (`cycle_number`).
   - The Ledger journal layer enforces deduplication on the **internal payment voucher** (`clearance_voucher`), which is uniquely derived per cycle.
   - The Finalization endpoint closes the current batch, increments `current_cycle`, and returns the channel state to `IDLE`.
   - The cryptographic Ed25519 signature on the sovereign manifest is valid indefinitely and is never permanently bound to a single cycle.

3. **Multi-Stage Lifecycle Progression**:
   An attacker cannot simply replay an isolated HTTP request. Advancing through the concentric rings requires executing:
   `POST /api/pipeline/intake` → `POST /api/pipeline/earmark` → `POST /api/pipeline/disburse` → `POST /api/receipts/finalize`
   in strict sequential order.

4. **Accounting Solvency & Supervisory Trigger**:
   Draining the reserve pool below the statutory adequacy floor (`250.00 SDR`) puts the channel into a critical deficit state. Calling `POST /api/channel/reconcile` on the drained channel triggers the emergency regulatory intervention protocol, releasing the contingency attestation seal containing the flag.

---

## Organizer Hints (For Release if Teams are Blocked)

1. *Observation Hint (30 mins)*:
   "Inspect the network traffic during a complete 4-ring clearance. Notice how the channel returns to IDLE after finalizing a batch, but the clearing cycle counter advances. Does the treasury manifest specify a cycle number?"
2. *State Hint (45 mins)*:
   "What checks does Ring I perform compared to Ring III? Can a previously accepted sovereign manifest be accepted again once a batch has been finalized into a certificate?"
3. *Objective Hint (60 mins)*:
   "Check the dashboard gauge for the Statutory Reserve Floor. What happens when the sovereign liquidity pool reserve falls below 250 SDR and supervisory reconciliation is requested?"
