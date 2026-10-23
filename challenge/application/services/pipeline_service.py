import time
import json
from sqlalchemy.orm import Session
from models.channel import SettlementChannel
from models.staging import CycleStagingRecord
from models.journal import LedgerJournalEntry
from models.receipt import SettlementCertificate
from core.crypto import verify_manifest_signature
from core.security import derive_earmark_ticket, derive_clearance_voucher, compute_integrity_checksum

class PipelineException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def process_intake(
    db: Session,
    channel: SettlementChannel,
    manifest: dict,
    authority_key: str,
    signature: str
) -> dict:
    if channel.pipeline_stage != "IDLE":
        raise PipelineException(
            "ERR_STAGE_OCCUPIED",
            f"Pipeline stage '{channel.pipeline_stage}' must be 'IDLE' to accept new settlement instructions",
            status_code=409
        )

    if not verify_manifest_signature(manifest, authority_key, signature):
        raise PipelineException(
            "ERR_ATTESTATION_INVALID",
            "Cryptographic signature validation failure against sovereign authority registry",
            status_code=400
        )

    valid_until = manifest.get("valid_until", 0)
    if valid_until < int(time.time()):
        raise PipelineException(
            "ERR_INSTRUCTION_EXPIRED",
            "The presented settlement manifest has passed its statutory validity horizon",
            status_code=400
        )

    instruction_ref = manifest.get("instruction_ref")
    if not instruction_ref:
        raise PipelineException(
            "ERR_MALFORMED_MANIFEST",
            "Settlement manifest lacks mandatory instruction reference identifier",
            status_code=400
        )

    quantum = float(manifest.get("quantum", 0.0))
    if quantum <= 0:
        raise PipelineException(
            "ERR_INVALID_QUANTUM",
            "Instruction quantum must represent a positive numerical settlement value",
            status_code=400
        )

    duplicate_in_cycle = db.query(CycleStagingRecord).filter(
        CycleStagingRecord.channel_id == channel.channel_id,
        CycleStagingRecord.cycle_number == channel.current_cycle,
        CycleStagingRecord.instruction_ref == instruction_ref
    ).first()

    if duplicate_in_cycle:
        raise PipelineException(
            "ERR_INSTRUCTION_DUPLICATE_IN_CYCLE",
            f"Instruction reference '{instruction_ref}' is already staged for settlement cycle {channel.current_cycle}",
            status_code=409
        )

    ticket = derive_earmark_ticket(channel.channel_id, channel.current_cycle, instruction_ref)

    channel.pipeline_stage = "INTAKE_VALIDATED"
    channel.active_instruction_ref = instruction_ref
    channel.active_ticket = ticket
    channel.active_quantum = quantum

    staging_record = CycleStagingRecord(
        channel_id=channel.channel_id,
        cycle_number=channel.current_cycle,
        instruction_ref=instruction_ref,
        staged_at=int(time.time()),
        earmark_ticket=ticket,
        status="STAGED"
    )
    db.add(staging_record)
    db.commit()
    db.refresh(channel)

    return {
        "status": "INTAKE_ACCEPTED",
        "channel_id": channel.channel_id,
        "cycle_number": channel.current_cycle,
        "instruction_ref": instruction_ref,
        "earmark_ticket": ticket,
        "quantum": quantum,
        "pipeline_stage": channel.pipeline_stage
    }

def process_earmark(db: Session, channel: SettlementChannel, ticket: str) -> dict:
    if channel.pipeline_stage != "INTAKE_VALIDATED":
        raise PipelineException(
            "ERR_INVALID_TRANSITION",
            f"Cannot allocate collateral while channel is in stage '{channel.pipeline_stage}'",
            status_code=409
        )

    if ticket != channel.active_ticket:
        raise PipelineException(
            "ERR_TICKET_MISMATCH",
            "Earmark ticket presented does not match active cycle reservation",
            status_code=403
        )

    if channel.reserve_balance < channel.active_quantum:
        raise PipelineException(
            "ERR_LIQUIDITY_EXHAUSTED",
            "Insufficient sovereign pool reserve to earmark requested quantum",
            status_code=400
        )

    voucher = derive_clearance_voucher(ticket)

    channel.pipeline_stage = "RESERVE_EARMARKED"
    channel.active_voucher = voucher
    db.commit()
    db.refresh(channel)

    return {
        "status": "COLLATERAL_EARMARKED",
        "channel_id": channel.channel_id,
        "cycle_number": channel.current_cycle,
        "earmark_ticket": ticket,
        "clearance_voucher": voucher,
        "earmarked_quantum": channel.active_quantum,
        "pipeline_stage": channel.pipeline_stage
    }

def process_disburse(db: Session, channel: SettlementChannel, voucher: str) -> dict:
    if channel.pipeline_stage != "RESERVE_EARMARKED":
        raise PipelineException(
            "ERR_INVALID_TRANSITION",
            f"Cannot disburse settlement while channel is in stage '{channel.pipeline_stage}'",
            status_code=409
        )

    if voucher != channel.active_voucher:
        raise PipelineException(
            "ERR_VOUCHER_MISMATCH",
            "Clearance voucher presented does not match active earmark authorization",
            status_code=403
        )

    existing_entry = db.query(LedgerJournalEntry).filter(
        LedgerJournalEntry.voucher_ref == voucher
    ).first()

    if existing_entry:
        raise PipelineException(
            "ERR_VOUCHER_COMMITTED",
            "Clearance voucher has already posted a debit entry to the double-entry journal",
            status_code=409
        )

    now = int(time.time())
    journal_id = f"JRN-{channel.channel_id[:8].upper()}-{now}-{channel.current_cycle}"
    entry_data = f"{journal_id}:{voucher}:{channel.active_quantum}:{now}"
    entry_hash = compute_integrity_checksum(entry_data)

    channel.reserve_balance -= channel.active_quantum
    channel.channel_balance += channel.active_quantum
    channel.pipeline_stage = "DISBURSED"

    journal_entry = LedgerJournalEntry(
        journal_id=journal_id,
        channel_id=channel.channel_id,
        cycle_number=channel.current_cycle,
        voucher_ref=voucher,
        source_account="POOL:CHAKRA:RESERVE",
        destination_account=f"CHANNEL:{channel.channel_id}",
        units=channel.active_quantum,
        posted_at=now,
        entry_hash=entry_hash
    )
    db.add(journal_entry)
    db.commit()
    db.refresh(channel)

    return {
        "status": "DISBURSEMENT_COMMITTED",
        "journal_id": journal_id,
        "voucher_ref": voucher,
        "units_disbursed": channel.active_quantum,
        "new_channel_balance": channel.channel_balance,
        "remaining_reserve": channel.reserve_balance,
        "pipeline_stage": channel.pipeline_stage
    }

def process_finalization(db: Session, channel: SettlementChannel) -> dict:
    if channel.pipeline_stage != "DISBURSED":
        raise PipelineException(
            "ERR_INVALID_TRANSITION",
            f"Cannot finalize settlement cycle while channel is in stage '{channel.pipeline_stage}'",
            status_code=409
        )

    cycle_entries = db.query(LedgerJournalEntry).filter(
        LedgerJournalEntry.channel_id == channel.channel_id,
        LedgerJournalEntry.cycle_number == channel.current_cycle
    ).all()

    total_cleared = sum(e.units for e in cycle_entries)
    journal_refs = [e.journal_id for e in cycle_entries]

    now = int(time.time())
    cert_id = f"CERT-{channel.channel_id[:8].upper()}-CYC{channel.current_cycle}-{now}"
    cert_hash = compute_integrity_checksum(f"{cert_id}:{total_cleared}:{now}")

    certificate = SettlementCertificate(
        certificate_id=cert_id,
        channel_id=channel.channel_id,
        cycle_number=channel.current_cycle,
        total_cleared=total_cleared,
        journal_references=json.dumps(journal_refs),
        issued_at=now,
        integrity_hash=cert_hash
    )
    db.add(certificate)

    # Archive active cycle staging record
    staged_records = db.query(CycleStagingRecord).filter(
        CycleStagingRecord.channel_id == channel.channel_id,
        CycleStagingRecord.cycle_number == channel.current_cycle
    ).all()
    for rec in staged_records:
        rec.status = "ARCHIVED"

    completed_cycle = channel.current_cycle
    channel.current_cycle += 1
    channel.pipeline_stage = "IDLE"
    channel.active_instruction_ref = None
    channel.active_ticket = None
    channel.active_voucher = None
    channel.active_quantum = None

    db.commit()
    db.refresh(channel)

    return {
        "status": "BATCH_FINALITY_CONFIRMED",
        "certificate_id": cert_id,
        "completed_cycle": completed_cycle,
        "total_units_cleared": total_cleared,
        "integrity_hash": cert_hash,
        "next_cycle": channel.current_cycle,
        "pipeline_stage": channel.pipeline_stage
    }
