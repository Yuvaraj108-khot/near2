from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from application.database import Base

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(String(32), unique=True, index=True, nullable=False)
    account_id = Column(String(32), index=True, nullable=False)
    settlement_id = Column(String(32), index=True, nullable=False)
    order_id = Column(String(32), index=True, nullable=False)
    quote_ref = Column(String(64), index=True, nullable=False)
    entry_type = Column(String(32), default="DISBURSEMENT", nullable=False)
    debit_account = Column(String(64), default="RESERVE_POOL", nullable=False)
    credit_account = Column(String(64), default="SOLVER_SETTLEMENT_ACCOUNT", nullable=False)
    amount = Column(Float, nullable=False)
    reserve_after = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
