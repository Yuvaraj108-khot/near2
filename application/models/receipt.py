from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from application.database import Base

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(String(32), unique=True, index=True, nullable=False)
    receipt_identity = Column(String(64), unique=True, index=True, nullable=False)
    account_id = Column(String(32), index=True, nullable=False)
    settlement_id = Column(String(32), index=True, nullable=False)
    order_id = Column(String(32), index=True, nullable=False)
    quote_id = Column(String(32), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(32), default="SEALED", nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
