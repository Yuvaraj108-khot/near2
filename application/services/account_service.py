import secrets
from sqlalchemy.orm import Session
from application.models.account import SolverAccount
from application.models.order import MarketOrder
from application.core.security import generate_solver_token
from application.config import settings

def create_solver_account(db: Session, solver_name: str) -> SolverAccount:
    account_id = f"SLV-{secrets.token_hex(4).upper()}"
    token = generate_solver_token()

    account = SolverAccount(
        account_id=account_id,
        token=token,
        solver_name=solver_name or f"Solver-{account_id}",
        balance=0.0,
        reserve_balance=settings.INITIAL_POOL_RESERVE,
        solvency_floor=settings.STATUTORY_SOLVENCY_FLOOR
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    # Seed competitive clearing orders for this solver session
    seed_orders = [
        MarketOrder(
            account_id=account_id,
            order_id="ORD-801",
            pair="USDC/ETH",
            nominal_size=1000.0,
            base_rate=1.05,
            target_fee_bps=180,
            status="OPEN"
        ),
        MarketOrder(
            account_id=account_id,
            order_id="ORD-802",
            pair="SOL/USDC",
            nominal_size=1400.0,
            base_rate=1.02,
            target_fee_bps=160,
            status="OPEN"
        ),
        MarketOrder(
            account_id=account_id,
            order_id="ORD-803",
            pair="NEAR/USDT",
            nominal_size=1800.0,
            base_rate=1.08,
            target_fee_bps=200,
            status="OPEN"
        )
    ]
    db.add_all(seed_orders)
    db.commit()

    return account

def get_account_profile(db: Session, account: SolverAccount) -> dict:
    from application.models.settlement import Settlement
    from application.models.receipt import Receipt
    from application.models.quote import Quote

    settlements_count = db.query(Settlement).filter_by(account_id=account.account_id).count()
    receipts_count = db.query(Receipt).filter_by(account_id=account.account_id).count()
    quotes_count = db.query(Quote).filter_by(account_id=account.account_id).count()

    return {
        "account_id": account.account_id,
        "solver_name": account.solver_name,
        "balance": round(account.balance, 4),
        "reserve_balance": round(account.reserve_balance, 4),
        "solvency_floor": round(account.solvency_floor, 4),
        "reserve_ratio": round(account.reserve_balance / settings.INITIAL_POOL_RESERVE, 4),
        "total_quotes": quotes_count,
        "total_settlements": settlements_count,
        "total_receipts": receipts_count,
        "created_at": account.created_at.isoformat()
    }
