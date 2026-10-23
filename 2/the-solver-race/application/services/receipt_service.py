import secrets
from typing import Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from application.models.settlement import Settlement
from application.models.receipt import Receipt
from application.models.quote import Quote
from application.models.order import MarketOrder
from application.models.account import SolverAccount
from application.core.hashing import compute_receipt_identity

def issue_settlement_receipt(db: Session, account: SolverAccount, settlement_id: str) -> Dict[str, Any]:
    settlement = db.query(Settlement).filter_by(
        account_id=account.account_id,
        settlement_id=settlement_id
    ).first()

    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement '{settlement_id}' not found."
        )

    # Derive receipt identity bound to logical root quote ID
    receipt_identity = compute_receipt_identity(
        account.account_id,
        settlement.order_id,
        settlement.quote_id
    )

    existing_receipt = db.query(Receipt).filter_by(receipt_identity=receipt_identity).first()
    if existing_receipt:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ERR_RECEIPT_ALREADY_ISSUED: Clearance certificate already issued for root quote '{settlement.quote_id}'."
        )

    receipt_id = f"RCT-{secrets.token_hex(4).upper()}"
    receipt = Receipt(
        receipt_id=receipt_id,
        receipt_identity=receipt_identity,
        account_id=account.account_id,
        settlement_id=settlement.settlement_id,
        order_id=settlement.order_id,
        quote_id=settlement.quote_id,
        amount=settlement.amount,
        status="SEALED"
    )
    db.add(receipt)

    # Seal root quote into archival state
    quote = db.query(Quote).filter_by(
        account_id=account.account_id,
        quote_id=settlement.quote_id
    ).first()
    if quote:
        quote.state = "ARCHIVED"

    # Mark market order as filled
    order = db.query(MarketOrder).filter_by(
        account_id=account.account_id,
        order_id=settlement.order_id
    ).first()
    if order:
        order.status = "SETTLED"

    db.commit()

    return {
        "receipt_id": receipt.receipt_id,
        "receipt_identity": receipt.receipt_identity,
        "settlement_id": receipt.settlement_id,
        "order_id": receipt.order_id,
        "quote_id": receipt.quote_id,
        "amount": receipt.amount,
        "status": receipt.status,
        "issued_at": receipt.issued_at.isoformat()
    }

def get_receipt(db: Session, account_id: str, receipt_id: str) -> Dict[str, Any]:
    receipt = db.query(Receipt).filter_by(
        account_id=account_id,
        receipt_id=receipt_id
    ).first()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt '{receipt_id}' not found."
        )

    return {
        "receipt_id": receipt.receipt_id,
        "receipt_identity": receipt.receipt_identity,
        "settlement_id": receipt.settlement_id,
        "order_id": receipt.order_id,
        "quote_id": receipt.quote_id,
        "amount": receipt.amount,
        "status": receipt.status,
        "issued_at": receipt.issued_at.isoformat()
    }

def list_receipts(db: Session, account_id: str) -> List[Dict[str, Any]]:
    receipts = db.query(Receipt).filter_by(account_id=account_id).order_by(Receipt.id.desc()).all()
    return [
        {
            "receipt_id": r.receipt_id,
            "receipt_identity": r.receipt_identity,
            "settlement_id": r.settlement_id,
            "order_id": r.order_id,
            "quote_id": r.quote_id,
            "amount": r.amount,
            "status": r.status,
            "issued_at": r.issued_at.isoformat()
        }
        for r in receipts
    ]
