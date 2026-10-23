import time
from sqlalchemy.orm import Session
from models.channel import SettlementChannel
from core.security import generate_channel_id
from config import DEFAULT_INITIAL_RESERVE, STATUTORY_RESERVE_FLOOR

def create_channel(db: Session, participant_urn: str = "urn:vyuha:participant:default") -> SettlementChannel:
    channel = SettlementChannel(
        channel_id=generate_channel_id(),
        created_at=int(time.time()),
        participant_urn=participant_urn,
        current_cycle=1,
        pipeline_stage="IDLE",
        channel_balance=0.0,
        reserve_balance=DEFAULT_INITIAL_RESERVE
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel

def get_channel(db: Session, channel_id: str) -> SettlementChannel | None:
    return db.query(SettlementChannel).filter(SettlementChannel.channel_id == channel_id).first()

def get_channel_telemetry(channel: SettlementChannel) -> dict:
    reserve_ratio = channel.reserve_balance / DEFAULT_INITIAL_RESERVE
    return {
        "channel_id": channel.channel_id,
        "participant_urn": channel.participant_urn,
        "current_cycle": channel.current_cycle,
        "pipeline_stage": channel.pipeline_stage,
        "channel_balance": channel.channel_balance,
        "reserve_balance": channel.reserve_balance,
        "reserve_ratio": round(reserve_ratio, 4),
        "statutory_floor": STATUTORY_RESERVE_FLOOR,
        "active_instruction_ref": channel.active_instruction_ref,
        "active_ticket": channel.active_ticket,
        "active_voucher": channel.active_voucher,
        "active_quantum": channel.active_quantum
    }
