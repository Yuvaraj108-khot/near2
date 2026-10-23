from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from application.database import Base

class ReconciliationAudit(Base):
    __tablename__ = "reconciliation_audits"

    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(32), unique=True, index=True, nullable=False)
    account_id = Column(String(32), index=True, nullable=False)
    total_settlements = Column(Integer, nullable=False)
    total_disbursed = Column(Float, nullable=False)
    pool_reserve = Column(Float, nullable=False)
    solvency_floor = Column(Float, nullable=False)
    receipt_count = Column(Integer, nullable=False)
    solvency_status = Column(String(32), nullable=False)
    certificate_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
