import os
from dotenv import load_dotenv
import requests

load_dotenv()

REGION = os.getenv("WOW_REGION", "us")
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")

def get_token():
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET)
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def check_item(item_id, token):
    url = f"https://{REGION}.api.blizzard.com/data/wow/item/{item_id}"
    params = {
        "namespace": f"static-{REGION}",
        "locale": "en_US",
        "access_token": token
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    print(f"item_id={item_id} | name={data.get('name')} | quality={data.get('quality')} | level={data.get('level')}")

if __name__ == "__main__":
    token = get_token()
    for item_id in [236774, 236775]:
        try:
            check_item(item_id, token)
        except requests.exceptions.HTTPError as e:
            print(f"item_id={item_id} | ERROR: {e}")