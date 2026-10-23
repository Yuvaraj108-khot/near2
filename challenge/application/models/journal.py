from sqlalchemy import Column, String, Integer, Float
from database import Base

class LedgerJournalEntry(Base):
    __tablename__ = "ledger_journal_entries"

    journal_id = Column(String(64), primary_key=True, index=True)
    channel_id = Column(String(64), index=True, nullable=False)
    cycle_number = Column(Integer, nullable=False)
    voucher_ref = Column(String(64), unique=True, index=True, nullable=False)
    source_account = Column(String(64), nullable=False)
    destination_account = Column(String(64), nullable=False)
    units = Column(Float, nullable=False)
    posted_at = Column(Integer, nullable=False)
    entry_hash = Column(String(64), nullable=False)
