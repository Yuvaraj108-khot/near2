import secrets
import hashlib

def generate_channel_id() -> str:
    return "chn_" + secrets.token_hex(12)

def derive_earmark_ticket(channel_id: str, cycle_number: int, instruction_ref: str) -> str:
    raw = f"{channel_id}:{cycle_number}:{instruction_ref}:{secrets.token_hex(8)}"
    return "TCK-" + hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24].upper()

def derive_clearance_voucher(ticket: str) -> str:
    raw = f"VOUCHER:{ticket}:{secrets.token_hex(8)}"
    return "VCHR-" + hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24].upper()

def compute_integrity_checksum(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
