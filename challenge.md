# Chakravyuh Sovereign Settlement Gateway

**Category**: Web / Fintech Protocols  
**Difficulty**: Medium  
**Points**: 175  

> The Vyūha Clearing Engine orchestrates sovereign inter-institution liquidity settlements across concentric rings of validation. Built on the Saptaratha settlement architecture, every settlement instruction submitted to the clearinghouse is cryptographically attested by the sovereign liquidity vault, strictly ordered, and committed to double-entry ledger journals.
>
> Your institution has been allocated an operational settlement channel backed by pooled sovereign liquidity reserves. Clear funds through the concentric rings, monitor reserve adequacy against statutory requirements, and maintain institutional compliance with clearinghouse supervisory oversight.

---

## Service Overview

The gateway provides both an interactive web terminal at `/` and a REST API for automated institutional integration:

```http
POST /api/channel/open               Initialize an operational clearing channel
GET  /api/channel/status             Query channel balance, stage, and reserve ratio
GET  /api/instructions/manifest      Retrieve pre-authorized sovereign treasury manifest
POST /api/pipeline/intake            Submit signed settlement manifest for Ring I intake
POST /api/pipeline/earmark           Authorize Ring II collateral reservation
POST /api/pipeline/disburse          Execute Ring III double-entry ledger mutation
POST /api/receipts/finalize          Seal Ring IV batch and issue settlement certificate
POST /api/channel/reconcile          Trigger supervisory reserve and capital compliance review
```

---

## Connection

The application is deployed at:

```
http://<HOST>:<PORT>/
```

A live institutional dashboard is available in your browser at the root path, providing visual telemetry for all active settlement rings, collateral allocations, and journal entries.

---

## Rules of Engagement

- The cryptographic attestation mechanism uses sovereign Ed25519 signing keys. Tampered manifests or modified authorization keys are strictly invalid.
- Avoid brute forcing or denial-of-service traffic; all protocol operations can be explored with standard HTTP requests or the web console.
- In accordance with standard clearinghouse governance, operational channels must maintain statutory capital adequacy relative to the sovereign pool reserve floor.
