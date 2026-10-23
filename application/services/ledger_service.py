from sqlalchemy.orm import Session
from models.journal import LedgerJournalEntry
from models.receipt import SettlementCertificate

def get_channel_journals(db: Session, channel_id: str) -> list[dict]:
    entries = db.query(LedgerJournalEntry).filter(
        LedgerJournalEntry.channel_id == channel_id
    ).order_by(LedgerJournalEntry.posted_at.desc()).all()

    return [
        {
            "journal_id": e.journal_id,
            "cycle_number": e.cycle_number,
            "voucher_ref": e.voucher_ref,
            "source_account": e.source_account,
            "destination_account": e.destination_account,
            "units": e.units,
            "posted_at": e.posted_at,
            "entry_hash": e.entry_hash
        }
        for e in entries
    ]

def search_channel_journals(db: Session, channel_id: str, query: str) -> list[dict]:
    entries = db.query(LedgerJournalEntry).filter(
        LedgerJournalEntry.channel_id == channel_id
    ).all()

    q = query.lower()
    filtered = [
        e for e in entries
        if q in e.journal_id.lower() or q in e.voucher_ref.lower() or q in str(e.units)
    ]

    return [
        {
            "journal_id": e.journal_id,
            "cycle_number": e.cycle_number,
            "voucher_ref": e.voucher_ref,
            "units": e.units,
            "posted_at": e.posted_at
        }
        for e in filtered
    ]

def get_channel_certificates(db: Session, channel_id: str) -> list[dict]:
    certs = db.query(SettlementCertificate).filter(
        SettlementCertificate.channel_id == channel_id
    ).order_by(SettlementCertificate.issued_at.desc()).all()

    return [
        {
            "certificate_id": c.certificate_id,
            "cycle_number": c.cycle_number,
            "total_cleared": c.total_cleared,
            "issued_at": c.issued_at,
            "integrity_hash": c.integrity_hash
        }
        for c in certs
    ]
