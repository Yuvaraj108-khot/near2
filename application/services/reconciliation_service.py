import time
from sqlalchemy.orm import Session
from models.channel import SettlementChannel
from models.receipt import SupervisoryAuditLog
from config import DEFAULT_INITIAL_RESERVE, STATUTORY_RESERVE_FLOOR, SETTLEMENT_ATTESTATION_SEAL

def perform_supervisory_reconciliation(db: Session, channel: SettlementChannel) -> dict:
    reserve_ratio = channel.reserve_balance / DEFAULT_INITIAL_RESERVE
    now = int(time.time())

    if channel.reserve_balance >= STATUTORY_RESERVE_FLOOR:
        audit_log = SupervisoryAuditLog(
            audit_id=f"AUD-{channel.channel_id[:8].upper()}-{now}",
            channel_id=channel.channel_id,
            timestamp=now,
            reserve_level=channel.reserve_balance,
            reserve_ratio=round(reserve_ratio, 4),
            evaluation="MARGIN_ADEQUATE",
            intervention_reference=None,
            attestation_seal=None
        )
        db.add(audit_log)
        db.commit()

        return {
            "status": "RECONCILIATION_COMPLIANT",
            "channel_id": channel.channel_id,
            "cycle_evaluated": channel.current_cycle,
            "reserve_ratio": round(reserve_ratio, 4),
            "statutory_floor": STATUTORY_RESERVE_FLOOR,
            "variance": 0.0,
            "status_assessment": "MARGIN_ADEQUATE",
            "clearance_authorization": "NORMAL_OPERATIONS"
        }
    else:
        intervention_ref = f"INT-{channel.channel_id[:8].upper()}-{now}"
        audit_log = SupervisoryAuditLog(
            audit_id=f"AUD-{channel.channel_id[:8].upper()}-{now}",
            channel_id=channel.channel_id,
            timestamp=now,
            reserve_level=channel.reserve_balance,
            reserve_ratio=round(reserve_ratio, 4),
            evaluation="CRITICAL_DEFICIT",
            intervention_reference=intervention_ref,
            attestation_seal=SETTLEMENT_ATTESTATION_SEAL
        )
        db.add(audit_log)
        db.commit()

        return {
            "status": "RECONCILIATION_DEFICIT_TRIGGERED",
            "channel_id": channel.channel_id,
            "cycle_evaluated": channel.current_cycle,
            "reserve_ratio": round(reserve_ratio, 4),
            "statutory_floor": STATUTORY_RESERVE_FLOOR,
            "variance": round(channel.reserve_balance - STATUTORY_RESERVE_FLOOR, 2),
            "status_assessment": "CRITICAL_DEFICIT",
            "clearance_authorization": "SUSPENDED_FOR_INSPECTION",
            "contingency_resolution": {
                "record_urn": f"urn:vyuha:supervisory:contingency:{channel.channel_id[:8]}",
                "attestation_anchor": SETTLEMENT_ATTESTATION_SEAL,
                "regulatory_directive": "STATUTORY_CAPITAL_INJECTION_REQUIRED",
                "action_epoch": now
            }
        }
