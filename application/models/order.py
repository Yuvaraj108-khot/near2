from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from application.database import Base

class MarketOrder(Base):
    __tablename__ = "market_orders"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(32), index=True, nullable=False)
    order_id = Column(String(32), index=True, nullable=False)
    pair = Column(String(32), nullable=False)
    nominal_size = Column(Float, nullable=False)
    base_rate = Column(Float, nullable=False)
    target_fee_bps = Column(Integer, default=150, nullable=False)
    status = Column(String(32), default="OPEN", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
