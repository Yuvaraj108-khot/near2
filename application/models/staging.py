from sqlalchemy import Column, String, Integer
from database import Base

class CycleStagingRecord(Base):
    __tablename__ = "cycle_staging_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(64), index=True, nullable=False)
    cycle_number = Column(Integer, nullable=False)
    instruction_ref = Column(String(64), nullable=False)
    staged_at = Column(Integer, nullable=False)
    earmark_ticket = Column(String(64), nullable=False)
    status = Column(String(32), default="STAGED", nullable=False)
