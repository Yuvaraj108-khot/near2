from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from application.database import Base
from application.config import settings

class SolverAccount(Base):
    __tablename__ = "solver_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(32), unique=True, index=True, nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    solver_name = Column(String(64), nullable=False)
    balance = Column(Float, default=0.0, nullable=False)
    reserve_balance = Column(Float, default=settings.INITIAL_POOL_RESERVE, nullable=False)
    solvency_floor = Column(Float, default=settings.STATUTORY_SOLVENCY_FLOOR, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
