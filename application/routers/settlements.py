from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.settlement_service import (
    execute_settlement,
    get_settlement,
    list_settlements
)

router = APIRouter(prefix="/settlements", tags=["Settlements"])

class SettlementRequest(BaseModel):
    quote_ref: str

@router.post("")
def create_settlement(
    req: SettlementRequest,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return execute_settlement(
        db=db,
        account=current_solver,
        quote_ref=req.quote_ref
    )

@router.get("")
def get_all_settlements(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return list_settlements(db, current_solver.account_id)

@router.get("/{settlement_id}")
def get_settlement_by_id(
    settlement_id: str,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return get_settlement(db, current_solver.account_id, settlement_id)
