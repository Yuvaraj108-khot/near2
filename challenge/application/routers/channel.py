from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.channel_service import create_channel, get_channel, get_channel_telemetry

router = APIRouter(prefix="/api/channel", tags=["Channel"])

class OpenChannelRequest(BaseModel):
    participant_urn: str = "urn:vyuha:participant:node-1"

class SettingsRequest(BaseModel):
    channel_id: str
    notification_webhook: str | None = None
    telemetry_interval: int | None = 60

@router.post("/open")
def open_channel_endpoint(req: OpenChannelRequest = OpenChannelRequest(), db: Session = Depends(get_db)):
    channel = create_channel(db, req.participant_urn)
    return {
        "status": "CHANNEL_INITIALIZED",
        "channel_id": channel.channel_id,
        "participant_urn": channel.participant_urn,
        "current_cycle": channel.current_cycle,
        "pipeline_stage": channel.pipeline_stage,
        "channel_balance": channel.channel_balance,
        "reserve_balance": channel.reserve_balance,
        "statutory_floor": 250.0
    }

@router.get("/status")
def channel_status_endpoint(channel_id: str = Query(...), db: Session = Depends(get_db)):
    channel = get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return get_channel_telemetry(channel)

@router.get("/profile")
def channel_profile_endpoint(channel_id: str = Query(...), db: Session = Depends(get_db)):
    channel = get_channel(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return {
        "channel_id": channel.channel_id,
        "participant_urn": channel.participant_urn,
        "created_at": channel.created_at,
        "routing_clearinghouse": "Chakra Sovereign Clearing Zone",
        "assigned_ring": "RING-ALPHA",
        "settlement_currency": "SDR",
        "regulatory_tier": "Tier-2 Participant",
        "active_cycle": channel.current_cycle
    }

@router.post("/settings")
def update_settings_endpoint(req: SettingsRequest, db: Session = Depends(get_db)):
    channel = get_channel(db, req.channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found in registry")
    return {
        "status": "SETTINGS_UPDATED",
        "channel_id": req.channel_id,
        "notification_webhook": req.notification_webhook,
        "telemetry_interval": req.telemetry_interval
    }
