from sqlalchemy import Column, String, Integer, Float
from database import Base

class SettlementChannel(Base):
    __tablename__ = "settlement_channels"

    channel_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(Integer, nullable=False)
    participant_urn = Column(String(128), nullable=False)
    current_cycle = Column(Integer, default=1, nullable=False)
    pipeline_stage = Column(String(32), default="IDLE", nullable=False)
    channel_balance = Column(Float, default=0.0, nullable=False)
    reserve_balance = Column(Float, default=1000.0, nullable=False)
    active_instruction_ref = Column(String(64), nullable=True)
    active_ticket = Column(String(64), nullable=True)
    active_voucher = Column(String(64), nullable=True)
    active_quantum = Column(Float, nullable=True)
