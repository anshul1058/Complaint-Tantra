#!/usr/bin/env python3
"""Stage 3: geocode unique pincodes via OpenStreetMap Nominatim (1 req/s, per policy).

Fills city + lat/long for rows that have a pincode but no city/geo yet.
Cache: data/raw/pin_geo_cache.json (resumable). Run after enrich; independent of scrape.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
STAGE1 = ROOT / "data" / "institutions_stage1.json"
CACHE = RAW / "pin_geo_cache.json"
UA = "ComplaintTantraDatasetBuilder/1.0 (educational open-data build; OSM/Nominatim)"


def nominatim_pin(pin: str) -> dict | None:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": f"{pin}, India", "format": "jsonv2", "addressdetails": 1, "limit": 1,
    })
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
    if not data:
        return {"found": False}
    r = data[0]
    addr = r.get("address", {})
    city = (addr.get("city") or addr.get("town") or addr.get("municipality")
            or addr.get("village") or "")
    return {"found": True, "lat": r["lat"], "lon": r["lon"], "city": city}


def main() -> int:
    rows = json.loads(STAGE1.read_text())
    pins = sorted({r["pincode"] for r in rows if r.get("pincode")})
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [p for p in pins if p not in cache]
    print(f"unique pins: {len(pins)}, cached: {len(cache)}, todo: {len(todo)}")
    for i, pin in enumerate(todo, 1):
        res = nominatim_pin(pin)
        if res and res.get("error"):
            print(f"{pin}: error {res['error']}")
            continue  # don't cache errors — will retry next run
        cache[pin] = res or {"found": False}
        CACHE.write_text(json.dumps(cache))
        if i % 50 == 0:
            print(f"{i}/{len(todo)}")
        time.sleep(1.1)
    print(f"done: {len(cache)} pins cached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
