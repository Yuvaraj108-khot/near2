from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.ledger_service import list_ledger_entries, get_ledger_summary

router = APIRouter(prefix="/ledger", tags=["Ledger"])

@router.get("")
def get_entries(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return list_ledger_entries(db, current_solver.account_id)

@router.get("/summary")
def get_summary(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return get_ledger_summary(db, current_solver)
