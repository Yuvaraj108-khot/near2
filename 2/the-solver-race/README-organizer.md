# Organizer Guide: The Solver Race

## Challenge Metadata

- **Title**: The Solver Race
- **Category**: Web
- **Difficulty**: 300 Points / Hard (College / University Level CTF)
- **Target Solve Time**: 45–90 minutes for a strong undergraduate web CTF player
- **AI-Resistance Rating**: 9/10 (Requires architectural comprehension of cross-service state and multi-tier object identities)
- **Flag Format**: `CHAKRAVYUHA{...}`
- **Flag**: `CHAKRAVYUHA{x_l4y3r_st4t3_1d3nt1ty_r3c0nc1l3_8f19}`

---

## 1. Concept & Vulnerability Overview

The challenge simulates a competitive algorithmic RFQ (Request for Quote) clearinghouse. Solvers compete to clear institutional orders against a finite liquidity reserve pool (initial reserve: 1500.00 CR, statutory solvency floor: 500.00 CR).

The vulnerability is a subtle **cross-service object identity and accounting inconsistency** between four modular subsystems:
1. **Quote Service**: Identifies standing quotes by the logical root quote ID (`quote_id`). Quotes allow legitimate adjustment before finality, creating new revision tickets (`quote_ref = f"{quote_id}:r{rev}"`).
2. **Settlement Service**: Derives operation uniqueness from the specific quote revision reference: `settlement_identity = hash(account_id, order_id, quote_ref)`. It enforces that no individual revision can settle twice.
3. **Ledger Service**: Debits the pool reserve and credits the solver's credited balance for every committed settlement execution.
4. **Receipt Service**: Derives clearance certificate uniqueness from the logical root quote: `receipt_identity = hash(account_id, order_id, quote_id)`. Sealing a receipt marks the quote permanently `ARCHIVED`.

### The Core Flaw
Because `SettlementService` keys duplicate protection on `quote_ref` (`QTE-xxx:r1`, `QTE-xxx:r2`) while `QuoteService` permits revisions on quotes that have not yet been permanently archived by `ReceiptService`, a solver can alternate:
```text
POST /api/quotes
    ↓
POST /api/settlements (r1)
    ↓
POST /api/quotes/{id}/adjust (mints r2)
    ↓
POST /api/settlements (r2)
    ↓
... (until pool reserve breaches the 500.00 CR statutory solvency floor)
    ↓
POST /api/reconciliation/audit (triggers emergency supervisory intervention certificate with flag)
```

Naive attacks fail:
- Replaying `POST /api/settlements` with the same quote revision fails with `409 Conflict: ERR_DUPLICATE_SETTLEMENT`.
- Issuing a receipt prematurely seals the quote into `ARCHIVED` status, permanently barring further adjustments.
- Direct flag requests or inspecting source variables are impossible because the flag is generated purely by the supervisory reconciliation engine upon detecting an authentic statutory solvency corridor breach.

---

## 2. Running the Challenge

### With Docker Compose (Recommended)

```bash
docker compose up --build
```
The service will be live at `http://localhost:8000/`.

### Locally with Python

```bash
pip install -r requirements.txt
uvicorn application.main:app --host 0.0.0.0 --port 8000
```

---

## 3. Automated Verification

The solution script in `organizer/solve.py` exercises the complete solver race sequence from a clean state and extracts the flag:

```bash
python organizer/solve.py http://localhost:8000
```

Expected output:
```text
[*] Initialized solver account: SLV-XXXX
[*] Created quote QTE-XXXX on ORD-801 (r1)
[*] Cycle 1 settled (Reserve: 1311.00 CR)
[*] Cycle 2 settled (Reserve: 1088.40 CR)
[*] Cycle 3 settled (Reserve: 831.60 CR)
[*] Cycle 4 settled (Reserve: 540.00 CR)
[*] Cycle 5 settled (Reserve: 213.00 CR)
[+] Statutory solvency floor breached! Current reserve: 213.00 CR < 500.00 CR
[+] Triggering supervisory reconciliation audit...
[+] Flag: CHAKRAVYUHA{x_l4y3r_st4t3_1d3nt1ty_r3c0nc1l3_8f19}
```

Detailed writeup and step-by-step discovery path are documented in `organizer/walkthrough.md`.
