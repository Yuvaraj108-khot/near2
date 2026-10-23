from typing import List, Optional
from sqlalchemy.orm import Session
from application.models.order import MarketOrder

def list_market_orders(db: Session, account_id: str) -> List[MarketOrder]:
    return db.query(MarketOrder).filter_by(account_id=account_id).all()

def get_market_order(db: Session, account_id: str, order_id: str) -> Optional[MarketOrder]:
    return db.query(MarketOrder).filter_by(account_id=account_id, order_id=order_id).first()
