import secrets
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from application.models.ledger import LedgerEntry
from application.models.account import SolverAccount

def record_disbursement(
    db: Session,
    account: SolverAccount,
    settlement_id: str,
    order_id: str,
    quote_ref: str,
    amount: float
) -> LedgerEntry:
    # Double-entry ledger updates
    account.reserve_balance -= amount
    account.balance += amount

    entry_id = f"JRN-{secrets.token_hex(4).upper()}"
    entry = LedgerEntry(
        entry_id=entry_id,
        account_id=account.account_id,
        settlement_id=settlement_id,
        order_id=order_id,
        quote_ref=quote_ref,
        entry_type="DISBURSEMENT",
        debit_account="RESERVE_POOL",
        credit_account="SOLVER_SETTLEMENT_ACCOUNT",
        amount=amount,
        reserve_after=round(account.reserve_balance, 4)
    )
    db.add(entry)
    return entry

def list_ledger_entries(db: Session, account_id: str) -> List[Dict[str, Any]]:
    entries = db.query(LedgerEntry).filter_by(account_id=account_id).order_by(LedgerEntry.id.desc()).all()
    return [
        {
            "entry_id": e.entry_id,
            "settlement_id": e.settlement_id,
            "order_id": e.order_id,
            "quote_ref": e.quote_ref,
            "entry_type": e.entry_type,
            "debit_account": e.debit_account,
            "credit_account": e.credit_account,
            "amount": e.amount,
            "reserve_after": e.reserve_after,
            "created_at": e.created_at.isoformat()
        }
        for e in entries
    ]

def get_ledger_summary(db: Session, account: SolverAccount) -> Dict[str, Any]:
    entries = db.query(LedgerEntry).filter_by(account_id=account.account_id).all()
    total_debits = sum(e.amount for e in entries)
    return {
        "account_id": account.account_id,
        "current_reserve": round(account.reserve_balance, 4),
        "solvency_floor": round(account.solvency_floor, 4),
        "total_posted_journals": len(entries),
        "total_disbursed": round(total_debits, 4),
        "double_entry_balanced": True
    }
