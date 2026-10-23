from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.channel_service import get_channel
from services.pipeline_service import process_finalization, PipelineException
from services.ledger_service import get_channel_certificates
from models.receipt import SettlementCertificate

router = APIRouter(prefix="/api/receipts", tags=["Receipts & Certificates"])

class FinalizeRequest(BaseModel):
    channel_id: str

@router.post("/finalize")
def finalize_cycle_endpoint(req: FinalizeRequest, db: Session = Depends(get_db)):
    channel = get_channel(db, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    try:
        return process_finalization(db, channel)
    except PipelineException as pe:
        raise HTTPException(status_code=pe.status_code, detail={"code": pe.code, "message": pe.message})

@router.get("/list")
def list_certificates_endpoint(channel_id: str = Query(...), db: Session = Depends(get_db)):
    channel = get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return get_channel_certificates(db, channel_id)

@router.get("/export")
def export_certificate_endpoint(
    channel_id: str = Query(...),
    cert_id: str = Query(...),
    db: Session = Depends(get_db)
):
    cert = db.query(SettlementCertificate).filter(
        SettlementCertificate.channel_id == channel_id,
        SettlementCertificate.certificate_id == cert_id
    ).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Settlement certificate not found")

    return {
        "statement_header": "CHAKRAVYUH CLEARING STATEMENT",
        "certificate_id": cert.certificate_id,
        "channel_id": cert.channel_id,
        "cycle_cleared": cert.cycle_number,
        "total_cleared_units": cert.total_cleared,
        "journal_disbursements": cert.journal_references,
        "timestamp": cert.issued_at,
        "cryptographic_integrity_seal": cert.integrity_hash
    }
