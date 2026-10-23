import os

APP_NAME = "Chakravyuh Sovereign Settlement Gateway"
PROTOCOL_VERSION = "CSP-v4.2"

DEFAULT_INITIAL_RESERVE = 1000.0
STATUTORY_RESERVE_FLOOR = 250.0
SETTLEMENT_QUANTUM = 150.0

# On Vercel serverless environment, filesystem is read-only except /tmp
default_db = "/tmp/settlement.db" if os.environ.get("VERCEL") else "settlement.db"
DB_PATH = os.environ.get("DB_PATH", default_db)

SETTLEMENT_ATTESTATION_SEAL = os.environ.get(
    "SETTLEMENT_ATTESTATION_SEAL",
    "CHAKRAVYUHA{s4pt4r4th4_cl34r1ng_st4t3_d3sync_x891b}"
)

# 32-byte deterministic seed for the sovereign treasury authority signing key
AUTHORITY_SEED_HEX = os.environ.get(
    "AUTHORITY_SEED_HEX",
    "4d616861626861726174615f536170746172617468615f56797568615f323032"
)
