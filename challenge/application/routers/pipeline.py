from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.channel_service import get_channel
from services.pipeline_service import (
    process_intake,
    process_earmark,
    process_disburse,
    PipelineException
)

router = APIRouter(prefix="/api/pipeline", tags=["Settlement Pipeline"])

class IntakeRequest(BaseModel):
    channel_id: str
    manifest: dict
    authority_key: str
    signature: str

class EarmarkRequest(BaseModel):
    channel_id: str
    ticket: str

class DisburseRequest(BaseModel):
    channel_id: str
    voucher: str

@router.post("/intake")
def pipeline_intake_endpoint(req: IntakeRequest, db: Session = Depends(get_db)):
    channel = get_channel(db, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    try:
        return process_intake(db, channel, req.manifest, req.authority_key, req.signature)
    except PipelineException as pe:
        raise HTTPException(status_code=pe.status_code, detail={"code": pe.code, "message": pe.message})

@router.post("/earmark")
def pipeline_earmark_endpoint(req: EarmarkRequest, db: Session = Depends(get_db)):
    channel = get_channel(db, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    try:
        return process_earmark(db, channel, req.ticket)
    except PipelineException as pe:
        raise HTTPException(status_code=pe.status_code, detail={"code": pe.code, "message": pe.message})

@router.post("/disburse")
def pipeline_disburse_endpoint(req: DisburseRequest, db: Session = Depends(get_db)):
    channel = get_channel(db, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    try:
        return process_disburse(db, channel, req.voucher)
    except PipelineException as pe:
        raise HTTPException(status_code=pe.status_code, detail={"code": pe.code, "message": pe.message})
