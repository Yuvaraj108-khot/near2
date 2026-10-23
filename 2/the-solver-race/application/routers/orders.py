from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.order_service import list_market_orders, get_market_order

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("")
def list_orders(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    orders = list_market_orders(db, current_solver.account_id)
    return [
        {
            "order_id": o.order_id,
            "pair": o.pair,
            "nominal_size": o.nominal_size,
            "base_rate": o.base_rate,
            "target_fee_bps": o.target_fee_bps,
            "status": o.status,
            "created_at": o.created_at.isoformat()
        }
        for o in orders
    ]

@router.get("/{order_id}")
def get_order_by_id(
    order_id: str,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    order = get_market_order(db, current_solver.account_id, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found."
        )
    return {
        "order_id": order.order_id,
        "pair": order.pair,
        "nominal_size": order.nominal_size,
        "base_rate": order.base_rate,
        "target_fee_bps": order.target_fee_bps,
        "status": order.status,
        "created_at": order.created_at.isoformat()
    }
