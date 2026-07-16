"""
Looks up real item IDs for a list of item names using Blizzard's own
item search endpoint (static namespace). Run this once to build your
real ITEM_BASKET list - don't hand-guess IDs from wikis.

Usage:
    python find_item_ids.py
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("WOW_REGION", "us")
STATIC_NAMESPACE = f"static-{REGION}"

BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")

# Names to look up - current Midnight-expansion tradeable materials.
# Edit this list as needed (add/remove herbs, ores, cloth, etc).
NAMES_TO_LOOKUP = [
    "Nocturnal Lotus",
    "Azeroot",
    "Sanguithorn",
    "Mana Lily",
    "Argentleaf",
    "Umbral Tin Ore",
    "Refulgent Copper Ore",
    "Dazzling Thorium",
    "Pure Loanite",
    "Bright Linen",
    "Arcanoweave",
    "Sunfire Silk",
]


def get_access_token() -> str:
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def search_item(access_token: str, name: str):
    resp = requests.get(
        f"https://{REGION}.api.blizzard.com/data/wow/search/item",
        params={
            "namespace": STATIC_NAMESPACE,
            "locale": "en_US",
            "name.en_US": name,
            "orderby": "id:desc",  # newest items first - Midnight items have high IDs
            "_pageSize": 50,
        },
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def main():
    token = get_access_token()
    found = {}

    for name in NAMES_TO_LOOKUP:
        results = search_item(token, name)
        # Exact (case-insensitive) name matches only - avoids picking up
        # unrelated items that happen to share a substring.
        exact = [
            r for r in results
            if r["data"]["name"]["en_US"].lower() == name.lower()
        ]
        if exact:
            item_id = exact[0]["data"]["id"]
            found[name] = item_id
            print(f"  MATCH   {name!r:25s} -> {item_id}")
        elif results:
            # No exact match - show the 5 highest-ID candidates (most likely
            # to be current-expansion items) for manual review
            candidates = [
                (r["data"]["id"], r["data"]["name"]["en_US"]) for r in results[:5]
            ]
            print(f"  UNSURE  {name!r:25s} -> no exact match, candidates: {candidates}")
        else:
            print(f"  MISS    {name!r:25s} -> no results")

    print("\n--- Paste this into config/items.py ---\n")
    print("ITEM_BASKET = [")
    for name, item_id in found.items():
        print(f"    {item_id},   # {name}")
    print("]")


if __name__ == "__main__":
    main()
