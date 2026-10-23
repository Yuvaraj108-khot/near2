import secrets
from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session
from application.database import get_db

def generate_solver_token() -> str:
    return f"slv_sec_{secrets.token_hex(20)}"

def get_current_solver(
    authorization: str = Header(None),
    x_solver_token: str = Header(None),
    db: Session = Depends(get_db)
):
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        else:
            token = authorization
    elif x_solver_token:
        token = x_solver_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing solver authorization token. Provide 'Authorization: Bearer <token>' or 'X-Solver-Token'."
        )

    # Delay import of SolverAccount to avoid circular import
    from application.models.account import SolverAccount
    account = db.query(SolverAccount).filter(SolverAccount.token == token).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired solver token."
        )

    return account
