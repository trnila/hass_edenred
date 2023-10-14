import base64
from hashlib import sha256

from aiohttp import ClientSession
import requests


class EdenredException(Exception):
    pass


async def get_balance(session: ClientSession, card_number: str, pan: str) -> float:
    h = sha256(pan.encode()).digest()
    hashed_pan = base64.b64encode(h).decode()

    # hardcoded in apk
    api_key = "UaDF#2JEAbp45B53bVmmgCsqRkTXk&PuLCfPT"
    headers = {
        "Authorization": f"ApiKey {api_key}",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; 2201117SY Build/TP1A.220624.014)",
    }

    response = await session.get(
        f"https://cz-tcbye-p.edenred.cz/api/v1/cards/{card_number}/balance?pan={requests.utils.quote(hashed_pan)}",
        headers=headers,
    )

    json = await response.json()
    if "title" in json:
        raise EdenredException(json["title"])
    for item in json["items"]:
        if item["walletType"] == "MAIN":
            return item["balance"]


if __name__ == "__main__":
    import argparse
    import asyncio

    async def main():
        p = argparse.ArgumentParser()
        p.add_argument("card_number", help="Serial number of the card")
        p.add_argument("pan", help="Last 4 digits of the card on front side")

        args = p.parse_args()

        async with ClientSession() as session:
            balance = await get_balance(session, args.card_number, args.pan)
            print(balance)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
