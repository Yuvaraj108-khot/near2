DIRECTORY_ENTRIES = {
    "VAULT-CHAKRA-PRIME": {
        "institution_name": "Chakra Sovereign Liquidity Vault Prime",
        "routing_urn": "urn:vyuha:vault:primary",
        "tier": "Tier-1 Sovereign Reserve",
        "settlement_currency": "SDR",
        "clearing_protocol": "CSP-v4.2",
        "status": "ONLINE_ACTIVE"
    },
    "SWIFT-IN-990": {
        "institution_name": "Indraprastha Interbank Gateway",
        "routing_urn": "urn:vyuha:member:in-990",
        "tier": "Tier-2 Clearing Member",
        "settlement_currency": "SDR",
        "clearing_protocol": "CSP-v4.2",
        "status": "ONLINE_ACTIVE"
    },
    "RTGS-DELHI-CENTRAL": {
        "institution_name": "Kurukshetra Central Clearing Facility",
        "routing_urn": "urn:vyuha:clearing:delhi",
        "tier": "Tier-1 Clearing House",
        "settlement_currency": "SDR",
        "clearing_protocol": "CSP-v4.2",
        "status": "ONLINE_ACTIVE"
    },
    "MUMBAI-CLEARING-NODE": {
        "institution_name": "Dwaraka Maritime Settlement Node",
        "routing_urn": "urn:vyuha:member:dwk-01",
        "tier": "Tier-2 Settlement Agent",
        "settlement_currency": "SDR",
        "clearing_protocol": "CSP-v4.2",
        "status": "ONLINE_ACTIVE"
    }
}

def lookup_directory(code: str) -> dict | None:
    return DIRECTORY_ENTRIES.get(code.upper())

def list_directory() -> list[dict]:
    return [
        {"code": k, **v} for k, v in DIRECTORY_ENTRIES.items()
    ]
