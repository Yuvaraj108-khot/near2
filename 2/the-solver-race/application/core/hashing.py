import hashlib
import json
from typing import Any, Dict

def canonical_hash(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA256 over canonical JSON string representation."""
    serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def compute_quote_signature(quote_ref: str, order_id: str, rate: float, payout_amount: float) -> str:
    data = {
        "order_id": order_id,
        "payout_amount": round(payout_amount, 4),
        "quote_ref": quote_ref,
        "rate": round(rate, 6)
    }
    return canonical_hash(data)

def compute_settlement_identity(account_id: str, order_id: str, quote_ref: str) -> str:
    """Settlement uniqueness derived from account, order, and exact quote revision reference."""
    data = {
        "account_id": account_id,
        "order_id": order_id,
        "quote_ref": quote_ref
    }
    return canonical_hash(data)

def compute_receipt_identity(account_id: str, order_id: str, quote_id: str) -> str:
    """Receipt clearance certificate uniqueness derived from account, order, and root quote ID."""
    data = {
        "account_id": account_id,
        "order_id": order_id,
        "quote_id": quote_id
    }
    return canonical_hash(data)
