"""
Blizzard Auction House Commodities - ingestion script.

Fetches an OAuth token via the client credentials flow, pulls region-wide
commodity auction data, filters to a fixed item basket, and loads new rows
into a local Postgres 'raw' table. Duplicate (snapshot_timestamp, item_id)
rows are silently skipped via ON CONFLICT DO NOTHING - safe to rerun.

Run manually for now:
    python ingest.py
"""

import os
import sys
from datetime import datetime, timezone

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from config.items import ITEM_BASKET

load_dotenv()

REGION = os.getenv("WOW_REGION", "us")
NAMESPACE = f"dynamic-{REGION}"
LOCALE = "en_US"

BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "wow_ah_raw")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")


def get_access_token() -> str:
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_commodities(access_token: str):
    url = f"https://{REGION}.api.blizzard.com/data/wow/auctions/commodities"
    params = {"namespace": NAMESPACE, "locale": LOCALE}
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    resp.raise_for_status()

    # Blizzard doesn't embed a snapshot time in the JSON body for this
    # endpoint. The Last-Modified header is the authoritative "as of" time -
    # use that as snapshot_timestamp, not our own request time, since our
    # poll schedule and Blizzard's roughly-hourly refresh schedule drift
    # relative to each other.
    last_modified = resp.headers.get("Last-Modified")
    if last_modified:
        snapshot_ts = datetime.strptime(
            last_modified, "%a, %d %b %Y %H:%M:%S %Z"
        ).replace(tzinfo=timezone.utc)
    else:
        snapshot_ts = datetime.now(timezone.utc)
        print("WARNING: no Last-Modified header returned; using request time instead")

    return resp.json(), snapshot_ts


def extract_rows(payload: dict, snapshot_ts: datetime):
    basket = set(ITEM_BASKET)
    rows = []
    debug_count = 0
    for auction in payload.get("auctions", []):
        item_id = auction["item"]["id"]
        if item_id not in basket:
            continue
        if debug_count < 5:
            print(auction["item"])  # TEMP DEBUG - remove after checking
            debug_count += 1
        rows.append(
            (
                snapshot_ts,
                auction["id"],
                item_id,
                auction.get("quantity"),
                auction.get("unit_price"),
            )
        )
    return rows


def load_rows(rows):
    if not rows:
        print("No matching rows this pull - nothing to insert.")
        return

    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    try:
        with conn, conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO raw_auction_commodities
                    (snapshot_timestamp, auction_id, item_id, quantity, unit_price)
                VALUES %s
                ON CONFLICT (snapshot_timestamp, auction_id) DO NOTHING
                """,
                rows,
            )
        print(f"Inserted up to {len(rows)} rows (duplicates silently skipped).")
    finally:
        conn.close()


def main():
    if not BLIZZARD_CLIENT_ID or not BLIZZARD_CLIENT_SECRET:
        sys.exit("Missing BLIZZARD_CLIENT_ID / BLIZZARD_CLIENT_SECRET in .env")

    token = get_access_token()
    payload, snapshot_ts = fetch_commodities(token)
    rows = extract_rows(payload, snapshot_ts)

    print(f"Snapshot timestamp (from Blizzard Last-Modified): {snapshot_ts.isoformat()}")
    matched_items = {r[2] for r in rows}  # r[2] is item_id in the row tuple
    print(f"Matched {len(rows)} individual auction listings "
          f"across {len(matched_items)} / {len(ITEM_BASKET)} basket items.")

    load_rows(rows)


if __name__ == "__main__":
    main()
