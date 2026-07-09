import os
import requests
from dotenv import load_dotenv

load_dotenv()
REGION = os.getenv("WOW_REGION", "us")
NAMESPACE = f"dynamic-{REGION}"
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")

# name -> (lower_id, higher_id). Higher id is whichever is currently in your basket.
PAIRS = {
    "Azeroot": (236774, 236775),
    "Sanguithorn": (236770, 236771),
    "Argentleaf": (236776, 236777),
    "Refulgent Copper Ore": (237359, 237361),
    "Bright Linen": (236963, 236965),
    "Arcanoweave": (237017, 237018),
    "Gloaming Alloy": (238202, 238203),
    "Sterling Alloy": (238204, 238205),
    "Mana Lily": (236778, 236779),
    "Infused Scalewoven Hide": (244633, 244634),
    "Sin'dorei Armor Banding": (244635, 244636),
    "Void-Tempered Plating": (238520, 238521),
}
def get_access_token():
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def main():
    token = get_access_token()
    resp = requests.get(
        f"https://{REGION}.api.blizzard.com/data/wow/auctions/commodities",
        params={"namespace": NAMESPACE, "locale": "en_US"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    all_ids = {tid for pair in PAIRS.values() for tid in pair}
    prices = {tid: [] for tid in all_ids}
    for auction in payload.get("auctions", []):
        item_id = auction["item"]["id"]
        if item_id in all_ids:
            prices[item_id].append(auction["unit_price"])

    print(f"{'Item':25s} {'Lower ID':>10s} {'min g':>10s} | {'Higher ID (basket)':>18s} {'min g':>10s}")
    for name, (low_id, high_id) in PAIRS.items():
        low_prices = prices[low_id]
        high_prices = prices[high_id]
        low_min = f"{min(low_prices)/10000:.2f}" if low_prices else "no data"
        high_min = f"{min(high_prices)/10000:.2f}" if high_prices else "no data"
        print(f"{name:25s} {low_id:>10d} {low_min:>10s} | {high_id:>18d} {high_min:>10s}")

if __name__ == "__main__":
    main()