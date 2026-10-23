from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from application.database import Base

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    settlement_id = Column(String(32), unique=True, index=True, nullable=False)
    settlement_identity = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(String(32), index=True, nullable=False)
    order_id = Column(String(32), index=True, nullable=False)
    quote_id = Column(String(32), index=True, nullable=False)
    quote_revision = Column(Integer, nullable=False)
    quote_ref = Column(String(64), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    state = Column(String(32), default="SETTLED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
