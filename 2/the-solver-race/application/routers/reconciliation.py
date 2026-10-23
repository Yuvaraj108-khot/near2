from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.reconciliation_service import (
    get_reconciliation_status,
    perform_reconciliation_audit
)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.get("/status")
def query_status(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return get_reconciliation_status(db, current_solver)

@router.post("/audit")
def run_audit(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return perform_reconciliation_audit(db, current_solver)
