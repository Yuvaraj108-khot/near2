from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.receipt_service import (
    issue_settlement_receipt,
    get_receipt,
    list_receipts
)

router = APIRouter(prefix="/receipts", tags=["Receipts"])

class ReceiptRequest(BaseModel):
    settlement_id: str

@router.post("")
def create_receipt(
    req: ReceiptRequest,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return issue_settlement_receipt(
        db=db,
        account=current_solver,
        settlement_id=req.settlement_id
    )

@router.get("")
def get_all_receipts(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return list_receipts(db, current_solver.account_id)

@router.get("/{receipt_id}")
def get_receipt_by_id(
    receipt_id: str,
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return get_receipt(db, current_solver.account_id, receipt_id)
