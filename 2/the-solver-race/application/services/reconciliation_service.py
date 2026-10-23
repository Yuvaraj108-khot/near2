import secrets
import json
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from application.models.account import SolverAccount
from application.models.settlement import Settlement
from application.models.receipt import Receipt
from application.models.ledger import LedgerEntry
from application.models.reconciliation import ReconciliationAudit
from application.config import settings

def get_reconciliation_status(db: Session, account: SolverAccount) -> Dict[str, Any]:
    settlements = db.query(Settlement).filter_by(account_id=account.account_id).all()
    receipts = db.query(Receipt).filter_by(account_id=account.account_id).all()
    ledger_entries = db.query(LedgerEntry).filter_by(account_id=account.account_id).all()

    total_disbursed = sum(s.amount for s in settlements)
    ledger_total = sum(l.amount for l in ledger_entries)

    is_deficit = account.reserve_balance < account.solvency_floor
    coverage_ratio = (
        round(account.reserve_balance / account.solvency_floor, 4)
        if account.solvency_floor > 0 else 1.0
    )

    return {
        "account_id": account.account_id,
        "current_reserve": round(account.reserve_balance, 4),
        "solvency_floor": round(account.solvency_floor, 4),
        "initial_reserve": settings.INITIAL_POOL_RESERVE,
        "total_disbursed": round(total_disbursed, 4),
        "ledger_total": round(ledger_total, 4),
        "total_settlements": len(settlements),
        "total_receipts": len(receipts),
        "liquidity_coverage_ratio": coverage_ratio,
        "solvency_status": "CRITICAL_DEFICIT" if is_deficit else "COMPLIANT",
        "audit_ready": True
    }

def perform_reconciliation_audit(db: Session, account: SolverAccount) -> Dict[str, Any]:
    settlements = db.query(Settlement).filter_by(account_id=account.account_id).all()
    receipts = db.query(Receipt).filter_by(account_id=account.account_id).all()
    ledger_entries = db.query(LedgerEntry).filter_by(account_id=account.account_id).all()

    total_disbursed = sum(s.amount for s in settlements)
    is_deficit = account.reserve_balance < account.solvency_floor
    audit_id = f"AUD-{secrets.token_hex(4).upper()}"

    if is_deficit:
        # Statutory Solvency Floor breached: issue emergency supervisory resolution certificate
        cert_id = f"CERT-RES-{secrets.token_hex(4).upper()}"
        certificate = {
            "certificate_id": cert_id,
            "issued_to": account.account_id,
            "solver_name": account.solver_name,
            "audit_timestamp": datetime.utcnow().isoformat(),
            "type": "SUPERVISORY_INTERVENTION_RESOLUTION",
            "reserve_status": "CRITICAL_DEFICIT",
            "recorded_reserve": round(account.reserve_balance, 4),
            "statutory_solvency_floor": round(account.solvency_floor, 4),
            "deficit_quantum": round(account.solvency_floor - account.reserve_balance, 4),
            "settlement_executions": len(settlements),
            "receipt_commitments": len(receipts),
            "resolution_mandate": "STATUTORY_BAIL_IN_CONTINGENCY",
            "attestation_seal": settings.FLAG,
            "clearance_statement": "Supervisory audit confirmed reserve breach below statutory floor. Contingency attestation certificate emitted."
        }
        status_label = "CRITICAL_DEFICIT"
    else:
        # Normal operational state
        cert_id = f"CERT-STD-{secrets.token_hex(4).upper()}"
        certificate = {
            "certificate_id": cert_id,
            "issued_to": account.account_id,
            "solver_name": account.solver_name,
            "audit_timestamp": datetime.utcnow().isoformat(),
            "type": "STANDARD_SUPERVISORY_CLEARANCE",
            "reserve_status": "COMPLIANT",
            "recorded_reserve": round(account.reserve_balance, 4),
            "statutory_solvency_floor": round(account.solvency_floor, 4),
            "settlement_executions": len(settlements),
            "receipt_commitments": len(receipts),
            "clearance_statement": "All clearing operations conform to standard solvency corridors."
        }
        status_label = "COMPLIANT"

    audit_record = ReconciliationAudit(
        audit_id=audit_id,
        account_id=account.account_id,
        total_settlements=len(settlements),
        total_disbursed=round(total_disbursed, 4),
        pool_reserve=round(account.reserve_balance, 4),
        solvency_floor=round(account.solvency_floor, 4),
        receipt_count=len(receipts),
        solvency_status=status_label,
        certificate_json=json.dumps(certificate)
    )
    db.add(audit_record)
    db.commit()

    return {
        "audit_id": audit_id,
        "solvency_status": status_label,
        "certificate": certificate
    }
