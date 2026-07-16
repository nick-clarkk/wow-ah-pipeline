import os
import requests
from dotenv import load_dotenv

load_dotenv()
REGION = os.getenv("WOW_REGION", "us")
STATIC_NAMESPACE = f"static-{REGION}"
BLIZZARD_CLIENT_ID = os.getenv("BLIZZARD_CLIENT_ID")
BLIZZARD_CLIENT_SECRET = os.getenv("BLIZZARD_CLIENT_SECRET")

def get_access_token():
    resp = requests.post(
        "https://oauth.battle.net/token",
        data={"grant_type": "client_credentials"},
        auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def check_item_detail(access_token, item_id):
    url = f"https://{REGION}.api.blizzard.com/data/wow/item/{item_id}"
    params = {"namespace": STATIC_NAMESPACE, "locale": "en_US"}
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 404:
        print(f"item_id={item_id} | 404 NOT FOUND")
    else:
        resp.raise_for_status()
        data = resp.json()
        print(f"item_id={item_id} | name={data.get('name')} | quality={data.get('quality')}")

def main():
    token = get_access_token()
    for item_id in [236778, 236779]:
        check_item_detail(token, item_id)

if __name__ == "__main__":
    main()