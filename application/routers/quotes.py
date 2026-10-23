from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.quote_service import (
    create_quote,
    adjust_quote,
    get_quote_details,
    list_quotes
)

router = APIRouter(prefix="/quotes", tags=["Quotes"])

class CreateQuoteRequest(BaseModel):
    order_id: str
    rate: Optional[float] = None
    spread_bps: Optional[int] = None
    allocation_pct: Optional[float] = 100.0

class AdjustQuoteRequest(BaseModel):
    rate_delta: Optional[float] = 0.0
    spread_delta: Optional[int] = 0
    allocation_pct: Optional[float] = None

@router.post("")
def post_quote(
    req: CreateQuoteRequest,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return create_quote(
        db=db,
        account_id=current_solver.account_id,
        order_id=req.order_id,
        rate=req.rate,
        spread_bps=req.spread_bps,
        allocation_pct=req.allocation_pct or 100.0
    )

@router.get("")
def get_all_quotes(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return list_quotes(db, current_solver.account_id)

@router.get("/{quote_id}")
def get_quote_by_id(
    quote_id: str,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return get_quote_details(db, current_solver.account_id, quote_id)

@router.post("/{quote_id}/adjust")
def adjust_existing_quote(
    quote_id: str,
    req: AdjustQuoteRequest,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return adjust_quote(
        db=db,
        account_id=current_solver.account_id,
        quote_id=quote_id,
        rate_delta=req.rate_delta,
        spread_delta=req.spread_delta,
        allocation_pct=req.allocation_pct
    )
