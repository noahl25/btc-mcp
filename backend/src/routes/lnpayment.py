import httpx
from src.database.redis import redis

async def get_usd_amount_in_sats(cents: int):
    cached = await redis.get("btc:sats_per_cent")
    if cached:
        return int(float(cached) * cents)

    async with httpx.AsyncClient(timeout=5) as client:
        r = await client.get("https://api.kraken.com/0/public/Ticker?pair=BTCUSD")
        r.raise_for_status()
        btc_price = float(r.json()["result"]["XXBTZUSD"]["c"][0])

    sats_per_cent = 100_000_000 * 0.01 / btc_price
    await redis.setex("btc:sats_per_cent", 600, sats_per_cent)
    return int(sats_per_cent * cents)