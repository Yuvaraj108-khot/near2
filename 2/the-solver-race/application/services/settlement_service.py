import secrets
from typing import Dict, Any, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from application.models.quote import Quote, QuoteRevision
from application.models.settlement import Settlement
from application.models.account import SolverAccount
from application.core.hashing import compute_settlement_identity, compute_quote_signature
from application.services.ledger_service import record_disbursement

def execute_settlement(db: Session, account: SolverAccount, quote_ref: str) -> Dict[str, Any]:
    revision = db.query(QuoteRevision).filter_by(
        account_id=account.account_id,
        quote_ref=quote_ref
    ).first()

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote revision '{quote_ref}' not found."
        )

    # Cryptographic integrity check on quote parameters
    expected_sig = compute_quote_signature(
        revision.quote_ref,
        revision.order_id,
        revision.rate,
        revision.payout_amount
    )
    if revision.signature != expected_sig:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quote cryptographic integrity attestation failed."
        )

    # Check settlement uniqueness derived from quote revision reference
    settlement_identity = compute_settlement_identity(
        account.account_id,
        revision.order_id,
        revision.quote_ref
    )

    existing_settlement = db.query(Settlement).filter_by(
        settlement_identity=settlement_identity
    ).first()

    if existing_settlement:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ERR_DUPLICATE_SETTLEMENT: Settlement operation already committed for quote reference '{quote_ref}'."
        )

    if revision.revision_state != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quote revision state is '{revision.revision_state}'. Only PENDING revisions may settle."
        )

    quote = db.query(Quote).filter_by(
        account_id=account.account_id,
        quote_id=revision.quote_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Root quote record missing."
        )

    if quote.state == "ARCHIVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot settle against ARCHIVED quote. Clearance receipt already finalized."
        )

    if account.reserve_balance < revision.payout_amount:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ERR_INSUFFICIENT_POOL_LIQUIDITY: Allocated channel reserve cannot cover settlement quantum."
        )

    # Record settlement
    settlement_id = f"STL-{secrets.token_hex(4).upper()}"
    settlement = Settlement(
        settlement_id=settlement_id,
        settlement_identity=settlement_identity,
        account_id=account.account_id,
        order_id=revision.order_id,
        quote_id=revision.quote_id,
        quote_revision=revision.revision_number,
        quote_ref=revision.quote_ref,
        amount=revision.payout_amount,
        state="SETTLED"
    )
    db.add(settlement)

    # Update revision & quote states
    revision.revision_state = "COMMITTED"
    quote.state = "SETTLED"

    # Commit double-entry ledger mutation
    ledger_entry = record_disbursement(
        db=db,
        account=account,
        settlement_id=settlement_id,
        order_id=revision.order_id,
        quote_ref=revision.quote_ref,
        amount=revision.payout_amount
    )

    db.commit()

    return {
        "settlement_id": settlement.settlement_id,
        "settlement_identity": settlement.settlement_identity,
        "order_id": settlement.order_id,
        "quote_ref": settlement.quote_ref,
        "amount": settlement.amount,
        "state": settlement.state,
        "ledger_entry_id": ledger_entry.entry_id,
        "credited_balance": round(account.balance, 4),
        "reserve_balance_after": round(account.reserve_balance, 4),
        "created_at": settlement.created_at.isoformat()
    }

def get_settlement(db: Session, account_id: str, settlement_id: str) -> Dict[str, Any]:
    settlement = db.query(Settlement).filter_by(
        account_id=account_id,
        settlement_id=settlement_id
    ).first()

    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement {settlement_id} not found."
        )

    return {
        "settlement_id": settlement.settlement_id,
        "settlement_identity": settlement.settlement_identity,
        "order_id": settlement.order_id,
        "quote_id": settlement.quote_id,
        "quote_revision": settlement.quote_revision,
        "quote_ref": settlement.quote_ref,
        "amount": settlement.amount,
        "state": settlement.state,
        "created_at": settlement.created_at.isoformat()
    }

def list_settlements(db: Session, account_id: str) -> List[Dict[str, Any]]:
    settlements = db.query(Settlement).filter_by(account_id=account_id).order_by(Settlement.id.desc()).all()
    return [
        {
            "settlement_id": s.settlement_id,
            "settlement_identity": s.settlement_identity,
            "order_id": s.order_id,
            "quote_id": s.quote_id,
            "quote_revision": s.quote_revision,
            "quote_ref": s.quote_ref,
            "amount": s.amount,
            "state": s.state,
            "created_at": s.created_at.isoformat()
        }
        for s in settlements
    ]
