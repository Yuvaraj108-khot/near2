# THE SOLVER RACE

**Category**: Web / Fintech Systems  
**Difficulty**: 300 Points  
**Format**: `CHAKRAVYUHA{...}`  

The settlement network is running its final supervisory reconciliation round.

Your solver account has been provisioned with access to the clearinghouse operations console and allocated a dedicated channel reserve backed by institutional liquidity.

Complete the assigned settlement workflow and obtain the final supervisory reconciliation certificate.

The clearinghouse exposes the standard HTTP interfaces used by all competing algorithmic market solvers.

---

### Challenge Access

Target: The challenge instance provided by the organizers (e.g. `http://localhost:8000`).

You may interact with the service through the Web Terminal at `http://localhost:8000/` or programmatically via the REST API endpoints:

```text
POST /api/account/register       Initialize solver session and provision clearing channel
GET  /api/account/profile        Inspect active session, credited balance, and reserve ratio
GET  /api/orders                 Query open institutional market settlement demands
POST /api/quotes                 Submit an operational settlement quote
GET  /api/quotes/{id}            Inspect quote terms and revision tickets
POST /api/quotes/{id}/adjust     Adjust standing quote parameters and recalibrate terms
POST /api/settlements            Execute settlement commitment against quote reference
GET  /api/settlements/{id}       Retrieve settlement execution record
POST /api/receipts               Seal settlement into clearance receipt certificate
GET  /api/receipts/{id}          Retrieve cryptographic clearance receipt
GET  /api/ledger                 Inspect posted double-entry journal records
GET  /api/reconciliation/status  Query statutory capital solvency telemetry
POST /api/reconciliation/audit   Execute supervisory reconciliation review and issue certificate
```
