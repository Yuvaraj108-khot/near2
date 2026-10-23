import secrets
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from application.models.quote import Quote, QuoteRevision
from application.models.order import MarketOrder
from application.core.hashing import compute_quote_signature

def calculate_payout(nominal_size: float, rate: float, spread_bps: int, allocation_pct: float) -> float:
    # Spread is calibrated in basis points with 1000 bps = 10.0% execution rebate
    gross = nominal_size * rate * (spread_bps / 1000.0)
    effective = gross * (allocation_pct / 100.0)
    return round(effective, 2)

def create_quote(
    db: Session,
    account_id: str,
    order_id: str,
    rate: Optional[float] = None,
    spread_bps: Optional[int] = None,
    allocation_pct: float = 100.0
) -> Dict[str, Any]:
    order = db.query(MarketOrder).filter_by(account_id=account_id, order_id=order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market order {order_id} not found."
        )

    effective_rate = rate if rate is not None else order.base_rate
    effective_spread = spread_bps if spread_bps is not None else order.target_fee_bps

    if effective_rate <= 0 or effective_spread <= 0 or allocation_pct <= 0 or allocation_pct > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pricing parameters for quote creation."
        )

    payout = calculate_payout(order.nominal_size, effective_rate, effective_spread, allocation_pct)

    quote_id = f"QTE-{secrets.token_hex(3).upper()}"
    quote_ref = f"{quote_id}:r1"
    sig = compute_quote_signature(quote_ref, order_id, effective_rate, payout)

    quote = Quote(
        quote_id=quote_id,
        account_id=account_id,
        order_id=order_id,
        current_revision=1,
        state="ACTIVE"
    )
    db.add(quote)

    revision = QuoteRevision(
        quote_id=quote_id,
        account_id=account_id,
        order_id=order_id,
        revision_number=1,
        quote_ref=quote_ref,
        rate=effective_rate,
        spread_bps=effective_spread,
        allocation_pct=allocation_pct,
        payout_amount=payout,
        revision_state="PENDING",
        signature=sig
    )
    db.add(revision)
    db.commit()

    return {
        "quote_id": quote.quote_id,
        "order_id": quote.order_id,
        "current_revision": quote.current_revision,
        "quote_ref": revision.quote_ref,
        "state": quote.state,
        "rate": revision.rate,
        "spread_bps": revision.spread_bps,
        "allocation_pct": revision.allocation_pct,
        "payout_amount": revision.payout_amount,
        "signature": revision.signature,
        "created_at": quote.created_at.isoformat()
    }

def adjust_quote(
    db: Session,
    account_id: str,
    quote_id: str,
    rate_delta: Optional[float] = 0.0,
    spread_delta: Optional[int] = 0,
    allocation_pct: Optional[float] = None
) -> Dict[str, Any]:
    quote = db.query(Quote).filter_by(account_id=account_id, quote_id=quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote {quote_id} not found."
        )

    if quote.state == "ARCHIVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot adjust quote. Quote has been permanently sealed into final clearance receipt archive."
        )

    order = db.query(MarketOrder).filter_by(account_id=account_id, order_id=quote.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Underlying market order not found."
        )

    latest_rev = db.query(QuoteRevision).filter_by(
        quote_id=quote.quote_id,
        revision_number=quote.current_revision
    ).first()

    if not latest_rev:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Revision state inconsistency."
        )

    new_rate = round(latest_rev.rate + (rate_delta or 0.0), 6)
    new_spread = max(20, latest_rev.spread_bps + (spread_delta or 0))
    new_alloc = allocation_pct if allocation_pct is not None else latest_rev.allocation_pct

    if new_rate <= 0 or new_alloc <= 0 or new_alloc > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjusted terms out of allowable corridor."
        )

    new_payout = calculate_payout(order.nominal_size, new_rate, new_spread, new_alloc)

    next_rev_num = quote.current_revision + 1
    new_quote_ref = f"{quote.quote_id}:r{next_rev_num}"
    sig = compute_quote_signature(new_quote_ref, quote.order_id, new_rate, new_payout)

    new_revision = QuoteRevision(
        quote_id=quote.quote_id,
        account_id=account_id,
        order_id=quote.order_id,
        revision_number=next_rev_num,
        quote_ref=new_quote_ref,
        rate=new_rate,
        spread_bps=new_spread,
        allocation_pct=new_alloc,
        payout_amount=new_payout,
        revision_state="PENDING",
        signature=sig
    )
    db.add(new_revision)

    quote.current_revision = next_rev_num
    quote.state = "ACTIVE"
    db.commit()

    return {
        "quote_id": quote.quote_id,
        "order_id": quote.order_id,
        "current_revision": quote.current_revision,
        "quote_ref": new_revision.quote_ref,
        "state": quote.state,
        "rate": new_revision.rate,
        "spread_bps": new_revision.spread_bps,
        "allocation_pct": new_revision.allocation_pct,
        "payout_amount": new_revision.payout_amount,
        "signature": new_revision.signature,
        "revision_number": next_rev_num
    }

def get_quote_details(db: Session, account_id: str, quote_id: str) -> Dict[str, Any]:
    quote = db.query(Quote).filter_by(account_id=account_id, quote_id=quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote {quote_id} not found."
        )

    revisions = db.query(QuoteRevision).filter_by(quote_id=quote_id).order_by(QuoteRevision.revision_number.asc()).all()

    return {
        "quote_id": quote.quote_id,
        "order_id": quote.order_id,
        "current_revision": quote.current_revision,
        "state": quote.state,
        "revisions": [
            {
                "revision_number": r.revision_number,
                "quote_ref": r.quote_ref,
                "rate": r.rate,
                "spread_bps": r.spread_bps,
                "allocation_pct": r.allocation_pct,
                "payout_amount": r.payout_amount,
                "revision_state": r.revision_state,
                "signature": r.signature,
                "created_at": r.created_at.isoformat()
            }
            for r in revisions
        ],
        "created_at": quote.created_at.isoformat(),
        "updated_at": quote.updated_at.isoformat()
    }

def list_quotes(db: Session, account_id: str) -> List[Dict[str, Any]]:
    quotes = db.query(Quote).filter_by(account_id=account_id).all()
    results = []
    for q in quotes:
        active_rev = db.query(QuoteRevision).filter_by(quote_id=q.quote_id, revision_number=q.current_revision).first()
        results.append({
            "quote_id": q.quote_id,
            "order_id": q.order_id,
            "current_revision": q.current_revision,
            "state": q.state,
            "quote_ref": active_rev.quote_ref if active_rev else None,
            "payout_amount": active_rev.payout_amount if active_rev else 0.0,
            "rate": active_rev.rate if active_rev else 0.0,
            "spread_bps": active_rev.spread_bps if active_rev else 0,
            "created_at": q.created_at.isoformat()
        })
    return results
