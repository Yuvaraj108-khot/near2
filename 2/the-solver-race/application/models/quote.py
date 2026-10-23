from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from application.database import Base

class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(String(32), unique=True, index=True, nullable=False)
    account_id = Column(String(32), index=True, nullable=False)
    order_id = Column(String(32), index=True, nullable=False)
    current_revision = Column(Integer, default=1, nullable=False)
    state = Column(String(32), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class QuoteRevision(Base):
    __tablename__ = "quote_revisions"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(String(32), index=True, nullable=False)
    account_id = Column(String(32), index=True, nullable=False)
    order_id = Column(String(32), index=True, nullable=False)
    revision_number = Column(Integer, nullable=False)
    quote_ref = Column(String(64), unique=True, index=True, nullable=False)
    rate = Column(Float, nullable=False)
    spread_bps = Column(Integer, nullable=False)
    allocation_pct = Column(Float, nullable=False)
    payout_amount = Column(Float, nullable=False)
    revision_state = Column(String(32), default="PENDING", nullable=False)
    signature = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
