from sqlalchemy import Column, String, Integer, Float, Text
from database import Base

class SettlementCertificate(Base):
    __tablename__ = "settlement_certificates"

    certificate_id = Column(String(64), primary_key=True, index=True)
    channel_id = Column(String(64), index=True, nullable=False)
    cycle_number = Column(Integer, nullable=False)
    total_cleared = Column(Float, nullable=False)
    journal_references = Column(Text, nullable=False)
    issued_at = Column(Integer, nullable=False)
    integrity_hash = Column(String(64), nullable=False)

class SupervisoryAuditLog(Base):
    __tablename__ = "supervisory_audit_logs"

    audit_id = Column(String(64), primary_key=True, index=True)
    channel_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(Integer, nullable=False)
    reserve_level = Column(Float, nullable=False)
    reserve_ratio = Column(Float, nullable=False)
    evaluation = Column(String(64), nullable=False)
    intervention_reference = Column(String(64), nullable=True)
    attestation_seal = Column(String(128), nullable=True)
