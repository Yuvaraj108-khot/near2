from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from application.database import get_db
from application.core.security import get_current_solver
from application.models.account import SolverAccount
from application.services.account_service import create_solver_account, get_account_profile

router = APIRouter(prefix="/account", tags=["Account"])

class RegisterRequest(BaseModel):
    solver_name: Optional[str] = "AlphaSolver"

@router.post("/register")
def register_solver(req: RegisterRequest = None, db: Session = Depends(get_db)):
    name = req.solver_name if req else "AlphaSolver"
    account = create_solver_account(db, solver_name=name)
    return {
        "status": "SUCCESS",
        "account_id": account.account_id,
        "token": account.token,
        "solver_name": account.solver_name,
        "balance": account.balance,
        "reserve_balance": account.reserve_balance,
        "solvency_floor": account.solvency_floor,
        "message": "Solver account provisioned with dedicated liquidity reserve."
    }

@router.get("/profile")
def get_profile(
    current_solver: SolverAccount = Depends(get_current_solver),
    db: Session = Depends(get_db)
):
    return get_account_profile(db, current_solver)
