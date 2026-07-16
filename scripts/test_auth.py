"""
Standalone smoke test - confirms your Battle.net client credentials work
and that you can successfully call the commodities endpoint.

Does NOT touch Postgres. Run this first, before ingest.py.

Usage:
    python test_auth.py
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("WOW_REGION", "us")
NAMESPACE = f"dynamic-{REGION}"

BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")


def main():
    if not BLIZZARD_CLIENT_ID or not BLIZZARD_CLIENT_SECRET:
        sys.exit("Missing BLIZZARD_CLIENT_ID / BLIZZARD_CLIENT_SECRET - check your .env file")

    print("Step 1: requesting OAuth access token...")
    token_resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )

    if token_resp.status_code != 200:
        print(f"FAILED - status {token_resp.status_code}")
        print(token_resp.text)
        sys.exit(1)

    access_token = token_resp.json()["access_token"]
    print(f"  OK - got a token (expires in {token_resp.json().get('expires_in')}s)")

    print(f"\nStep 2: calling commodities endpoint (region={REGION})...")
    api_resp = requests.get(
        f"https://{REGION}.api.blizzard.com/data/wow/auctions/commodities",
        params={"namespace": NAMESPACE, "locale": "en_US"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )

    if api_resp.status_code != 200:
        print(f"FAILED - status {api_resp.status_code}")
        print(api_resp.text)
        sys.exit(1)

    data = api_resp.json()
    auctions = data.get("auctions", [])
    print(f"  OK - status 200, Last-Modified header: {api_resp.headers.get('Last-Modified')}")
    print(f"  Response contains {len(auctions)} total commodity listings")

    if auctions:
        sample = auctions[0]
        print(f"\n  Sample row: item_id={sample['item']['id']}, "
              f"quantity={sample.get('quantity')}, unit_price={sample.get('unit_price')}")

    print("\nAuth + API pull both working. Safe to move on to Postgres setup.")


if __name__ == "__main__":
    main()
