from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.channel_service import get_channel
from services.reconciliation_service import perform_supervisory_reconciliation
from models.receipt import SupervisoryAuditLog

router = APIRouter(prefix="", tags=["Reconciliation & Supervisory"])

class ReconcileRequest(BaseModel):
    channel_id: str

@router.post("/api/channel/reconcile")
@router.post("/api/settlement/reconcile")
def reconcile_channel_endpoint(req: ReconcileRequest, db: Session = Depends(get_db)):
    channel = get_channel(db, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return perform_supervisory_reconciliation(db, channel)

@router.get("/api/settlement/audit-history")
def audit_history_endpoint(channel_id: str = Query(...), db: Session = Depends(get_db)):
    channel = get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")

    logs = db.query(SupervisoryAuditLog).filter(
        SupervisoryAuditLog.channel_id == channel_id
    ).order_by(SupervisoryAuditLog.timestamp.desc()).all()

    return [
        {
            "audit_id": l.audit_id,
            "timestamp": l.timestamp,
            "reserve_level": l.reserve_level,
            "reserve_ratio": l.reserve_ratio,
            "evaluation": l.evaluation,
            "intervention_reference": l.intervention_reference
        }
        for l in logs
    ]
