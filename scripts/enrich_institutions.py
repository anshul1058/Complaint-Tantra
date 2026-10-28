#!/usr/bin/env python3
"""Stage 1: bulk web-sourced enrichment for institutions.

Inputs (data/raw/, all downloaded from public sources):
  all-institutions-with-programmes.json  AICTE approved list (GitHub mirror, scraped 2025-10-30)
  aishe_all.csv                          AISHE directory dump (arpitagarwala/indian-institutions-data)
  naac_valid_2025.xlsx                   NAAC valid-accreditation list as on 14-08-2025
  city_latlong.csv                       Indian city coordinates (recurze/IndianCities, OSM-derived)
  aicte_institutes_2016.pdf/.txt         aicte.gov.in Get_Institute_Id list (city + per-row page anchor)

Output: data/institutions_stage1.json
"""

import csv
import difflib
import json
import re
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "institutions_stage1.json"

AICTE_MIRROR_DATE = "2025-10-30"
PDF_URL = "https://www.aicte.gov.in/downloads/Get_Institute_Id.pdf"
DASHBOARD_URL = "https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved"

# AICTE Regional Committee jurisdictions: AICTE (constitution and functions of
# Regional Committees) Amendment Regulation 2000 (indiacode.gov.in) + current RO
# list (aicte.gov.in/contact/all). Guide's 6 labels; South Central (Hyderabad)
# folds into South (AP was Southern Committee per the 2000 regulation).
REGION = {
    "Chandigarh": "North", "Delhi": "North", "Haryana": "North",
    "Himachal Pradesh": "North", "Jammu and Kashmir": "North", "Punjab": "North",
    "Rajasthan": "North", "Uttar Pradesh": "North", "Uttarakhand": "North",
    "Andaman and Nicobar Islands": "South", "Andhra Pradesh": "South",
    "Telangana": "South", "Karnataka": "South", "Kerala": "South",
    "Puducherry": "South", "Tamil Nadu": "South", "Lakshadweep": "South",
    "Bihar": "East", "Jharkhand": "East", "Odisha": "East",
    "Sikkim": "East", "West Bengal": "East",
    "Dadra and Nagar Haveli": "West", "Daman and Diu": "West", "Goa": "West",
    "Gujarat": "West", "Maharashtra": "West",
    "Chhattisgarh": "Central", "Madhya Pradesh": "Central",
    "Arunachal Pradesh": "North-East", "Assam": "North-East",
    "Manipur": "North-East", "Meghalaya": "North-East", "Mizoram": "North-East",
    "Nagaland": "North-East", "Tripura": "North-East",
}

UNIVERSITY_JUNK = {"NOT APPLICABLE", "NONE", "N/A", "NA", "OTHER", "OTHERS", "NIL", "-"}


def norm_name(s: str) -> str:
    s = (s or "").upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = re.sub(
        r"\b(COLLEGE|COLLEGES|OF|THE|AND|INSTITUTE|INSTITUTES|TECHNOLOG\w*|ENGG|"
        r"ENGINEERING|POLYTECHNIC|SCHOOL|FOR|IN|AT|DEPT|DEPARTMENT|UNIVERSITY|"
        r"CAMPUS|GROUP|EDUCATIONAL|EDUCATION)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def state_in(text: str) -> str:
    t = (text or "").upper()
    for st in sorted(REGION, key=len, reverse=True):
        if st.upper() in t:
            return st
    for alt, canonical in [("JAMMU & KASHMIR", "Jammu and Kashmir"),
                           ("ORISSA", "Odisha"), ("PONDICHERRY", "Puducherry")]:
        if alt in t:
            return canonical
    return ""


def fix_site(site: str) -> str:
    site = (site or "").strip().lower()
    if not site or site in ("www", "-", "none", "nil", "na"):
        return ""
    site = site.strip(".,;()").replace(" ", "")
    if not site or "." not in site:
        return ""
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    try:
        p = urllib.parse.urlparse(site)
        if not re.search(r"\.[a-z]{2,}$", p.netloc):
            return ""
        return f"https://{p.netloc}{p.path}".rstrip("/")
    except ValueError:
        return ""


def load_naac() -> list[dict]:
    z = zipfile.ZipFile(RAW / "naac_valid_2025.xlsx")
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    ss = []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", ns):
        ss.append("".join(t.text or "" for t in si.iter(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
    rows = []
    for sheet in ("sheet1", "sheet2", "sheet3"):
        try:
            sh = ET.fromstring(z.read(f"xl/worksheets/{sheet}.xml"))
        except KeyError:
            continue
        data = []
        for r in sh.findall(".//m:row", ns):
            vals = []
            for c in r.findall("m:c", ns):
                v = c.find("m:v", ns)
                vals.append("" if v is None else (ss[int(v.text)] if c.get("t") == "s" else v.text))
            data.append(vals)
        if not data:
            continue
        hdr = data[0]
        for r in data[1:]:
            d = dict(zip(hdr, r))
            if "Current Grade" in d and d.get("HEI Name"):
                rows.append(d)
    return rows


def grade_of(d: dict) -> str:
    g = (d.get("Current Grade") or "").strip()
    return g if re.fullmatch(r"A\+\+|A\+|A|B\+\+|B\+|B|C", g) else ""


def build_index(rows: list[dict], name_key: str) -> tuple[dict, dict]:
    """Returns (exact_norm_index, {state: [norm_key,...]}) for fast fuzzy lookup."""
    exact: dict[str, list] = {}
    by_state: dict[str, list] = {}
    for r in rows:
        k = norm_name(r.get(name_key) or "")
        if not k:
            continue
        r["_n"] = k
        exact.setdefault(k, []).append(r)
        st = (r.get("_state") or "").upper()
        by_state.setdefault(st, []).append(k)
    for st in by_state:
        by_state[st] = sorted(set(by_state[st]))
    return exact, by_state


def _dmatch(a: str, b: str) -> bool:
    da = re.sub(r"[^A-Z0-9]", "", (a or "").upper())
    db = re.sub(r"[^A-Z0-9]", "", (b or "").upper())
    if not da or not db:
        return True
    if da == db:
        return True
    return difflib.SequenceMatcher(None, da, db).ratio() >= 0.90


def best_match(name: str, state: str, district: str, exact: dict, by_state: dict,
               cutoff: float, gate: bool):
    n = norm_name(name)
    if not n:
        return None
    state_u = state.upper()

    def in_state(c) -> bool:
        return (not state) or (c.get("_state") or "").upper() == state_u

    pool = [c for c in exact.get(n, []) if in_state(c)]
    if not pool:
        keys = by_state.get(state_u) if state else None
        if not keys:
            return None
        close = difflib.get_close_matches(n, keys, n=1, cutoff=cutoff)
        if not close:
            return None
        pool = [c for c in exact[close[0]] if in_state(c)]
    if not pool:
        return None
    if gate and district and len(pool) > 1:
        good = [c for c in pool if _dmatch(c.get("_district"), district)]
        if good:
            return good[0]
        # several same-state candidates, none district-matched: require strong name
        best = max(pool, key=lambda c: difflib.SequenceMatcher(None, n, c.get("_n", "")).ratio())
        if difflib.SequenceMatcher(None, n, best.get("_n", "")).ratio() >= 0.94:
            return best
        return None
    return pool[0]


def pdf_page_index() -> dict[str, int]:
    txt = (RAW / "aicte_institutes_2016.txt")
    if not txt.exists():
        return {}
    idx = {}
    for page, chunk in enumerate(txt.read_text(errors="replace").split("\f"), start=1):
        for m in re.finditer(r"\b1-\d+\b", chunk):
            idx.setdefault(m.group(0), page)
    return idx


def main() -> int:
    ours = json.loads((RAW / "all-institutions-with-programmes.json").read_text())
    print(f"aicte mirror: {len(ours)}")

    aishe = list(csv.DictReader((RAW / "aishe_all.csv").open()))
    for r in aishe:
        r["_state"] = r.get("stateName") or ""
        r["_district"] = r.get("districtName") or ""
    aishe_exact, aishe_by_state = build_index(aishe, "name")

    naac = load_naac()
    for r in naac:
        r["_state"] = state_in(r.get("Address") or "")
        r["_district"] = ""
    naac_exact, naac_by_state = build_index(naac, "HEI Name")
    print(f"aishe: {len(aishe)} rows, naac: {len(naac)} rows")

    city_geo = list(csv.DictReader((RAW / "city_latlong.csv").open()))
    geo_city, geo_dist = {}, {}
    for r in city_geo:
        if not r["Latitude"] or r["Latitude"] == "0":
            continue
        try:
            lat, lon = float(r["Latitude"]), float(r["Longitude"])
        except ValueError:
            continue
        st = (r["State"] or "").replace("&", "and")
        key_c = (st.upper(), (r["City"] or "").upper())
        key_d = (st.upper(), (r["District"] or "").upper())
        geo_city.setdefault(key_c, (lat, lon, r["City"], "city"))
        geo_dist.setdefault(key_d, (lat, lon, r["District"], "district"))

    pages = pdf_page_index()
    pdf_ids = set(pages)
    print(f"pdf page anchors: {len(pdf_ids)}")

    pdf_cities = {}
    if (RAW / "aicte_institutes_2016.txt").exists():
        pending = None
        for raw in (RAW / "aicte_institutes_2016.txt").read_text(errors="replace").splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            parts = [p for p in re.split(r"\s{2,}", line.strip()) if p]
            if pending:
                if len(parts) >= 3:
                    pdf_cities[pending] = parts[-1].strip()
                pending = None
                continue
            if len(parts) >= 5 and re.match(r"^1-\d+$", parts[0]):
                pdf_cities[parts[0]] = parts[-1].strip()
            elif len(parts) == 2 and re.match(r"^1-\d+$", parts[0]):
                pending = parts[0]

    stats = dict(aishe=0, website=0, year=0, naac=0, geo=0, geo_dist=0, city=0, uni_fixed=0)
    out, seen = [], set()
    # duplicate groups (name+district+state) for possible-duplicate notes
    def dkey(o):
        return (norm_name(o["institute_name"]), (o.get("district") or "").upper(),
                (o.get("state") or "").upper())
    groups: dict[tuple, list] = {}
    for o in ours:
        groups.setdefault(dkey(o), []).append(o)
    dup_second_ids = set()
    for g in groups.values():
        if len(g) > 1:
            # strong duplicate signal: identical course sets
            course_sets = {tuple(sorted(p.get("course", "") for p in x.get("programmes", []))) for x in g}
            if len(course_sets) < len(g) and len(course_sets) == 1:
                for x in g[1:]:
                    dup_second_ids.add(x["aicte_id"])

    for rec in ours:
        aid = (rec.get("aicte_id") or "").strip()
        if not aid or aid in seen:
            continue
        seen.add(aid)
        name = (rec.get("institute_name") or "").strip()
        state = (rec.get("state") or "").strip()
        district = (rec.get("district") or "").strip()
        address = (rec.get("address") or "").strip()
        addr_parts = [p.strip() for p in address.split(",") if p.strip()]

        row = {
            "aicte_id": aid,
            "other_id": rec.get("other_id") or "",
            "institution_name": name,
            "institute_type_raw": (rec.get("institution_type") or "").strip(),
            "state": state,
            "district": district,
            "address_line1": addr_parts[0] if addr_parts else "",
            "address_line2": ", ".join(addr_parts[1:]) if len(addr_parts) > 1 else "",
            "women": (rec.get("women") or "").strip().upper(),
            "minority": (rec.get("minority") or "").strip().upper() == "Y",
            "university": (rec.get("university") or "").strip(),
            "programmes": rec.get("programmes") or [],
            "website": "",
            "year_of_establishment": "",
            "naac_grade": "",
            "pincode": "",
            "latitude": "",
            "longitude": "",
            "geo_precision": "",
            "city": "",
            "phone": "",
            "mobile": "",
            "email": "",
            "principal_name": "",
            "hostel_available": "",
            "trust_name": "",
            "notes": [],
        }
        m = re.search(r"\b\d{6}\b", address)
        if m:
            row["pincode"] = m.group(0)

        a = best_match(name, state, district, aishe_exact, aishe_by_state, 0.86, gate=True)
        if a:
            stats["aishe"] += 1
            site = fix_site(a.get("webSite") or "")
            if site:
                row["website"] = site
                stats["website"] += 1
            yr = (a.get("yearOfEstablishment") or "").strip()
            if re.fullmatch(r"(18|19|20)\d{2}", yr):
                row["year_of_establishment"] = yr
                stats["year"] += 1
            if not row["pincode"]:
                pm = re.search(r"\b\d{6}\b", a.get("address1") or "")
                if pm:
                    row["pincode"] = pm.group(0)
            uni = (a.get("universityName") or "").strip()
            if row["university"].upper() in UNIVERSITY_JUNK and uni \
                    and uni.upper() not in UNIVERSITY_JUNK:
                row["university"] = uni
                stats["uni_fixed"] += 1

        # junk values must go even when no AISHE match was found
        if row["university"].upper() in UNIVERSITY_JUNK:
            row["university"] = ""

        n = best_match(name, state, district, naac_exact, naac_by_state, 0.86, gate=False)
        if n:
            g = grade_of(n)
            if g:
                row["naac_grade"] = g
                stats["naac"] += 1
            if not row["pincode"]:
                pm = re.search(r"\b\d{6}\b", n.get("Address") or "")
                if pm:
                    row["pincode"] = pm.group(0)

        city = ""
        oid = rec.get("other_id") or ""
        if oid in pdf_cities:
            city = pdf_cities[oid]
            stats["city"] += 1
        row["city"] = city

        geo = None
        if city:
            geo = geo_city.get((state.upper(), city.upper()))
        if not geo:
            geo = geo_dist.get((state.upper(), district.upper()))
            if geo:
                stats["geo_dist"] += 1
        if geo:
            row["latitude"], row["longitude"] = f"{geo[0]:.6f}", f"{geo[1]:.6f}"
            row["geo_precision"] = geo[3]
            stats["geo"] += 1

        row["aicte_region"] = REGION.get(state, "")

        # provenance
        if oid in pages:
            row["source_url"] = f"{PDF_URL}#page={pages[oid]}"
        else:
            row["source_url"] = DASHBOARD_URL

        if row["minority"]:
            row["notes"].append("minority institution")
        if aid in dup_second_ids:
            row["notes"].append("possible duplicate listing (same name/district/courses)")
        if row["geo_precision"] == "city":
            row["notes"].append("lat/long = city centroid")
        elif row["geo_precision"] == "district":
            row["notes"].append("lat/long = district centroid")
        intake = sum(int(p["intake"]) for p in row["programmes"] if str(p.get("intake", "")).isdigit())
        if intake >= 20000:
            row["notes"].append("aggregate intake across campuses/programmes")
        row["notes"].append(f"AICTE approved list via mirror {AICTE_MIRROR_DATE}")
        row["_intake"] = intake

        out.append(row)

    OUT.write_text(json.dumps(out, ensure_ascii=False))
    print("stats:", stats)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
