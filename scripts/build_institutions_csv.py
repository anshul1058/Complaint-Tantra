#!/usr/bin/env python3
"""Build data/institutions.csv (header per Docs_md/institutions-csv-guide.md).

Pipeline:  enrich_institutions.py → scrape_sites.py → this script
Inputs:    data/institutions_stage1.json, data/site_cache.jsonl
Output:    data/institutions.csv   (UTF-8, exact 34-col header)

Self-checks run at the end (header/rows/states/blank-id/enum rules).
"""

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape_sites import EMAIL_BAD, PRINCIPAL_BAD, TRUST_KEYWORD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STAGE1 = DATA / "institutions_stage1.json"
CACHE = DATA / "site_cache.jsonl"
OUT = DATA / "institutions.csv"

HEADER = (
    "permanent_id,institution_name,short_name,institute_type,constitution,category,"
    "programmes_offered,total_approved_intake,approval_status,address_line1,address_line2,"
    "city,district,state,pincode,latitude,longitude,aicte_region,trust_name,campus_name,"
    "affiliated_university,phone,mobile,email,website,principal_name,year_of_establishment,"
    "approval_valid_till,nba_accredited,naac_grade,hostel_available,gender_policy,"
    "source_url,notes"
).split(",")

PDF_URL = "https://www.aicte.gov.in/downloads/Get_Institute_Id.pdf"
DASHBOARD_URL = "https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved"

INSTITUTE_TYPE = {
    "Government": "Govt",
    "State Government University": "Govt",
    "Central University": "Govt",
    "Govt aided": "Govt-Aided",
    "Private-Self Financing": "Self-Financed",
    "State Private University": "Private University",
    "Deemed to be University(Pvt)": "Deemed University",
    "Deemed to be University(Govt)": "Deemed University",
}

CATEGORY = {
    "ENGINEERING AND TECHNOLOGY": "Technical",
    "COMPUTER APPLICATIONS": "Technical",
    "COMPUTER APPLICATION": "Technical",
    "AI & DATA SCIENCE": "Technical",
    "MANAGEMENT": "Management",
    "MANAGEMENT/IT/ ITES": "Management",
    "TRAVEL & TOURISM": "Management",
    "LOGISTICS": "Management",
    "APPLIED ARTS AND CRAFTS": "Applied Arts",
    "DESIGN": "Applied Arts",
    "HOTEL MANAGEMENT AND CATERING": "Hotel Mgmt",
    "PLANNING": "Architecture",
}

DEGREE = {
    "ENGINEERING AND TECHNOLOGY": ("BTech", "MTech"),
    "COMPUTER APPLICATIONS": ("BCA", "MCA"),
    "COMPUTER APPLICATION": ("BCA", "MCA"),
    "MANAGEMENT": ("BBA", "MBA"),
    "MANAGEMENT/IT/ ITES": ("BBA", "MBA"),
    "PHARMACY": ("BPharm", "MPharm"),
    "ARCHITECTURE": ("BArch", "MArch"),
    "ARCHITECTURE AND TOWN PLANNING": ("BArch", "MArch"),
    "HOTEL MANAGEMENT AND CATERING": ("BHM", "MHM"),
    "DESIGN": ("BDes", "MDes"),
    "APPLIED ARTS AND CRAFTS": ("BFA", "MFA"),
    "PLANNING": ("BPlan", "MPlan"),
}

LEVEL_FIX = {
    "UNDER GRADUATE": "UG", "UG": "UG", "POST GRADUATE": "PG",
    "POST GRADUATE DIPLOMA": "PGDIP", "POST DIPLOMA": "PGDIP",
    "POST GRADUATE CERTIFICATE": "PGCERT", "DIPLOMA": "DIPLOMA",
    "FELLOWSHIP": "FELLOW", "INTEGRATED": "INTEGRATED",
    "BACHELOR OF VOCATION (B. VOC)": "BVOC", "DUALDEGREE": "DUAL",
}


def short_name(name: str) -> str:
    m = re.search(r"\(([^)]{2,20})\)\s*$", name)
    return m.group(1).strip() if m else ""


def degree_token(level: str, programme: str, course: str) -> str:
    lv = LEVEL_FIX.get(level.strip().upper(), level.strip().upper())
    pg = programme.strip().upper()
    if lv == "DIPLOMA":
        return "Diploma"
    if lv == "PGDIP":
        return "PGDip"
    if lv == "PGCERT":
        return "PGCert"
    if lv == "FELLOW":
        return "Fellow"
    if lv == "BVOC":
        return "BVoc"
    if lv in ("INTEGRATED", "DUAL"):
        return course.strip() or programme.strip()
    pair = DEGREE.get(pg)
    if pair and lv in ("UG", "PG"):
        return pair[0] if lv == "UG" else pair[1]
    return course.strip() or programme.strip()


def category_of(programmes: list) -> str:
    for p in programmes:
        cat = CATEGORY.get((p.get("programme") or "").strip().upper())
        if cat:
            return cat
    return "Technical" if programmes else ""


def blank_id(aicte_id: str) -> bool:
    """~25% missing permanent_id, deterministic (guide: matcher demo needs realistic gaps)."""
    return (sum(aicte_id.encode()) * 31 % 100) < 25


def load_cache() -> dict[str, dict]:
    out = {}
    if not CACHE.exists():
        return out
    for line in CACHE.read_text().splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        out[rec.get("url", "")] = rec
    return out


def load_pin_geo() -> dict[str, dict]:
    p = DATA / "raw" / "pin_geo_cache.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except ValueError:
        return {}


def live_source_url(row: dict, cache: dict[str, dict]) -> str:
    site = row.get("website") or ""
    rec = cache.get(site)
    if rec and rec.get("status") == 200:
        return rec.get("final_url") or site
    return row.get("source_url") or DASHBOARD_URL


def constitution_of(trust_name: str) -> str:
    if not trust_name:
        return ""
    if re.search(r"\bSociety\b", trust_name, re.I):
        return "Society"
    if re.search(r"\bTrust\b", trust_name, re.I):
        return "Trust"
    return ""


def main() -> int:
    stage1 = json.loads(STAGE1.read_text())
    cache = load_cache()
    pin_geo = load_pin_geo()
    print(f"stage1 rows: {len(stage1)}, cache entries: {len(cache)}, pins geo: {len(pin_geo)}")

    out_rows = []
    for row in stage1:
        site = row.get("website") or ""
        rec = cache.get(site, {})
        notes = list(row.get("notes") or [])
        if site and rec and rec.get("status") != 200:
            notes.append("website unreachable")
        elif site and not rec and cache:
            notes.append("website not yet verified")

        # pin → city / lat-lon backfill (Nominatim OSM), only into empty cells
        city = row.get("city", "")
        lat, lon = row.get("latitude", ""), row.get("longitude", "")
        pg = pin_geo.get(row.get("pincode") or "") or {}
        if pg.get("found"):
            if not city and pg.get("city"):
                city = pg["city"]
            if not lat:
                lat, lon = f"{float(pg['lat']):.6f}", f"{float(pg['lon']):.6f}"
                if not row.get("latitude") and row.get("pincode"):
                    notes.append("lat/long = pincode centroid")

        programmes = row.get("programmes") or []
        tokens = list(dict.fromkeys(
            degree_token(p.get("level", ""), p.get("programme", ""), p.get("course", ""))
            for p in programmes))
        intake = row.get("_intake") or sum(
            int(p["intake"]) for p in programmes if str(p.get("intake", "")).isdigit())
        trust = (rec.get("trust_name") or "").strip()
        if trust and not TRUST_KEYWORD.search(trust):
            trust = ""
        email = (rec.get("email") or "").strip()
        if email and EMAIL_BAD.search(email):
            email = ""
        principal = (rec.get("principal_name") or "").strip()
        if principal and PRINCIPAL_BAD.search(principal):
            principal = ""
        year = (rec.get("year_of_establishment") or "").strip() or row.get("year_of_establishment", "")
        pin = row.get("pincode") or rec.get("pincode") or ""
        if not pin and rec.get("pincode"):
            pin = rec["pincode"]

        out_rows.append({
            "permanent_id": "" if blank_id(row["aicte_id"]) else row["aicte_id"],
            "institution_name": row["institution_name"],
            "short_name": short_name(row["institution_name"]),
            "institute_type": INSTITUTE_TYPE.get(row.get("institute_type_raw", ""),
                                                 row.get("institute_type_raw", "")),
            "constitution": constitution_of(trust),
            "category": category_of(programmes),
            "programmes_offered": ";".join(tokens),
            "total_approved_intake": str(intake),
            "approval_status": "Approved",
            "address_line1": row.get("address_line1", ""),
            "address_line2": row.get("address_line2", ""),
            "city": city,
            "district": row.get("district", ""),
            "state": row.get("state", ""),
            "pincode": pin,
            "latitude": lat,
            "longitude": lon,
            "aicte_region": row.get("aicte_region", ""),
            "trust_name": trust,
            "campus_name": "",
            "affiliated_university": row.get("university", ""),
            "phone": (rec.get("phone") or "").strip(),
            "mobile": (rec.get("mobile") or "").strip(),
            "email": email,
            "website": site,
            "principal_name": principal,
            "year_of_establishment": year,
            "approval_valid_till": "",
            "nba_accredited": "",
            "naac_grade": row.get("naac_grade", ""),
            "hostel_available": (rec.get("hostel_available") or "").strip(),
            "gender_policy": {"Y": "girls-only", "N": "co-ed"}.get(row.get("women", ""), ""),
            "source_url": live_source_url(row, cache),
            "notes": "; ".join(notes),
        })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    # self-check (guide rules)
    with OUT.open(encoding="utf-8") as f:
        rdr = csv.reader(f)
        header = next(rdr)
        data = list(rdr)
    assert header == HEADER, "header mismatch"
    assert len(data) >= 500, f"only {len(data)} rows"
    states = {r[13] for r in data if r[13]}
    assert len(states) >= 20, f"only {len(states)} states"
    blank_pct = sum(1 for r in data if not r[0]) / len(data)
    assert 0.15 <= blank_pct <= 0.35, f"blank permanent_id {blank_pct:.0%} outside 15-35%"
    assert all(r[7].isdigit() for r in data), "non-numeric intake"
    assert all(r[17] in ("North", "South", "East", "West", "Central", "North-East", "")
               for r in data), "bad aicte_region"

    fill = {h: sum(1 for r in data if r[i]) for i, h in enumerate(header)}
    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(data)} rows, {len(states)} states, "
          f"blank permanent_id {blank_pct:.0%}")
    print("column fill:")
    for h in header:
        print(f"  {h:24s} {fill[h]*100//len(data):3d}%")
    empty = [h for h in header if fill[h] == 0]
    if empty:
        print("still empty:", ", ".join(empty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
