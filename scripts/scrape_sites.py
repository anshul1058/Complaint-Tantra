#!/usr/bin/env python3
"""Stage 2: polite scrape of college websites for contact/ownership fields.

Reads  data/institutions_stage1.json (rows with website)
Caches  data/site_cache.jsonl  (append-only, resumable — rerun skips cached URLs)
Extracts from homepage, plus one contact page when phone/email missing:
  phone, mobile, email, principal_name, year_of_establishment, hostel_available,
  trust_name, pincode (PIN-keyword only), verified source_url status

Run: python3 scripts/scrape_sites.py
"""

import concurrent.futures as cf
import html
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE1 = ROOT / "data" / "institutions_stage1.json"
CACHE = ROOT / "data" / "site_cache.jsonl"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 8
MAX_BYTES = 1_500_000
WORKERS = 8
CONTACT_PATHS = ("/contact-us", "/contact", "/contactus", "/contact-us.php")

CTX_VERIFIED = ssl.create_default_context()
CTX_INSECURE = ssl._create_unverified_context()

EMAIL_BAD = re.compile(
    r"(png|jpe?g|gif|svg|webp|css|js|ico|w3\.org|schema\.org|sentry|example|"
    r"yoursite|godaddy|wordpress|@localhost)", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PRINCIPAL_RE = re.compile(
    r"(Dr\.?|Prof\.?|Er\.?|Mr\.?|Ms\.?|Mrs\.?|Shri)\s+([A-Z][A-Za-z.'-]+(?:\s+(?:[A-Z][A-Za-z.'-]+|of|de|la)){1,3})")
PRINCIPAL_BAD = re.compile(
    r"College|Institute|University|Polytechnic|School|Message|Desk|Officer|"
    r"\bFrom\b|\bTo\b|\bThe\b|Trust|Society|Department|Dean|Director|Chairman|"
    r"Registrar|Dear|Council|Leadership|Office|Team|Committee|Board|Faculty|"
    r"Staff|\bHOD\b|\bCSE\b|\bECE\b|\bEEE\b", re.I)
YEAR_RE = re.compile(
    r"(?:Estd?\.?|Est\.?|Established|Since|Year\s+of\s+Establishment|Estd)\D{0,12}?"
    r"((?:19[0-9]|20[0-1])[0-9])", re.I)
PIN_RE = re.compile(r"(?:PIN(?:\s*Code)?\.?|Pincode)\s*[:\-]?\s*(\d{6})", re.I)
PHONE_RAW = re.compile(
    r"(?:\+?91[\s-]?)?(?:\(0\))?(?:0[\s-]?)?[1-9]\d[\d\s-]{6,12}\d")
TRUST_RE = re.compile(r"([A-Z][A-Za-z&'. -]{2,45})\s+(Trust|Society)\b")
TRUST_KEYWORD = re.compile(
    r"Educational|Education|Charitable|Welfare|Social|Shikshan|Vidya|"
    r"Samiti|Parisad|Group|Management|Foundation|Public Trust", re.I)
HOSTEL_RE = re.compile(r"\bhostels?\b", re.I)


def fetch(url: str) -> tuple[int, str, str]:
    """Returns (status, final_url, body_text_html). status -1 = network error."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
    })
    last = -1
    for ctx in (CTX_VERIFIED, CTX_INSECURE):
        try:
            with urllib.request.urlopen(req, timeout=7, context=ctx) as resp:
                raw = resp.read(MAX_BYTES)
                enc = (resp.headers.get("Content-Encoding") or "").lower()
                if enc == "gzip":
                    import gzip
                    try:
                        raw = gzip.decompress(raw)
                    except (OSError, EOFError, ValueError):
                        pass
                ctype = resp.headers.get("Content-Type") or ""
                if "html" not in ctype and "xml" not in ctype:
                    return resp.status, resp.geturl(), ""
                return resp.status, resp.geturl(), raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return e.code, url, ""
            last = e.code
        except ssl.SSLError:
            continue  # retry with insecure context
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return -1, url, ""  # unreachable — don't burn 4 attempts
    return last, url, ""


def visible_text(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|noscript|svg|head)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?s)<!--.*?-->", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(h))


def clean_site(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    p = urllib.parse.urlparse(url)
    if not p.netloc or "." not in p.netloc:
        return ""
    return f"https://{p.netloc}{p.path}".rstrip("/")


def extract(text: str) -> dict:
    out = {}

    emails = []
    for m in EMAIL_RE.finditer(text):
        e = m.group(0).lower().strip(".")
        if EMAIL_BAD.search(e) or e.count("@") != 1 or len(e) < 6:
            continue
        if e not in emails:
            emails.append(e)
    if emails:
        out["email"] = emails[0]

    phones = []
    for m in PHONE_RAW.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if not digits or len(digits) > 13:
            continue
        # normalize to 10-digit mobile (6-9 start) or STD landline (0 start)
        if digits.startswith("0091") and len(digits) >= 14:
            digits = digits[4:]
        if digits.startswith("91") and len(digits) in (12, 13):
            digits = digits[2:]
        if digits.startswith("0") and len(digits) in (11, 12):
            rest = digits[1:]
            if rest[0] in "6789":
                digits = rest  # 0 + 10-digit mobile
            else:
                if "phone" not in out:
                    out["phone"] = digits  # STD landline 0XX...
                continue
        if len(digits) == 10 and digits[0] in "6789":
            if "mobile" not in out:
                out["mobile"] = digits
        elif len(digits) >= 10 and digits[0] == "0":
            if "phone" not in out:
                out["phone"] = digits
        # anything else (e.g. year fragments like 202520261022) rejected
    # STD landline: 0XX-XXXX XXXX (11 digits starting 0, second digit 2-4)
    if "phone" not in out:
        for m in re.finditer(r"\b0[2-4]\d[\s-]?\d{6,8}\b", text):
            d = re.sub(r"\D", "", m.group(0))
            if 10 <= len(d) <= 12:
                out["phone"] = d
                break

    # principal: window around the word Principal
    for m in re.finditer(r"Principal", text):
        window = text[max(0, m.start() - 140): m.end() + 140]
        for pm in PRINCIPAL_RE.finditer(window):
            full = f"{pm.group(1).rstrip('.')} {pm.group(2)}".strip()
            if PRINCIPAL_BAD.search(pm.group(2)):
                continue
            if len(pm.group(2).split()) < 2:
                continue
            out["principal_name"] = re.sub(r"\s+", " ", full)
            break
        if "principal_name" in out:
            break
    if "principal_name" not in out:
        # "<Name>, Principal"
        m = re.search(r"([A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,3})\s*,?\s+Principal\b",
                      text)
        if m and not PRINCIPAL_BAD.search(m.group(1)):
            out["principal_name"] = m.group(1).strip()

    m = YEAR_RE.search(text)
    if m and 1900 <= int(m.group(1)) <= 2021:
        out["year_of_establishment"] = m.group(1)

    m = PIN_RE.search(text)
    if m:
        out["pincode"] = m.group(1)

    if HOSTEL_RE.search(text):
        out["hostel_available"] = "yes"

    for m in TRUST_RE.finditer(text):
        name = m.group(1).strip(" ,;.-")
        name = re.sub(r"^(?:Run by|Managed by|Managed|Established by|Promoted by|By)\s+",
                      "", name).strip()
        if len(name) < 4 or PRINCIPAL_BAD.search(name):
            continue
        if name.split()[0].lower() in ("the", "and", "of", "for", "a"):
            name = name.split(" ", 1)[1].strip() if " " in name else name
        if len(name.split()) >= 2:
            full = f"{name} {m.group(2)}"
            if TRUST_KEYWORD.search(full):
                out["trust_name"] = full
                break

    return out


def scrape_one(url: str) -> dict:
    try:
        return _scrape_one(url)
    except Exception as e:  # noqa: BLE001 — one bad site must not kill the run
        return {"url": url, "status": -1, "error": f"{type(e).__name__}: {e}"}


def _scrape_one(url: str) -> dict:
    rec = {"url": url}
    status, final, body = fetch(url)
    rec["status"] = status
    rec["final_url"] = final if status == 200 else url
    fields: dict = {}
    if status == 200 and body:
        fields = extract(visible_text(body))
        # follow one internal contact page when core contact missing
        if not fields.get("phone") and not fields.get("mobile") and not fields.get("email"):
            base = "{u.scheme}://{u.netloc}".format(u=urllib.parse.urlparse(final))
            for path in CONTACT_PATHS:
                cu = base + path
                st2, _, body2 = fetch(cu)
                if st2 == 200 and body2:
                    f2 = extract(visible_text(body2))
                    for k, v in f2.items():
                        fields.setdefault(k, v)
                    if fields.get("phone") or fields.get("mobile") or fields.get("email"):
                        rec["contact_url"] = cu
                        break
    rec.update(fields)
    return rec


def main() -> int:
    rows = json.loads(STAGE1.read_text())
    urls = sorted({clean_site(r["website"]) for r in rows if r.get("website")})
    urls = [u for u in urls if u]
    done: set[str] = set()
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            try:
                done.add(json.loads(line)["url"])
            except (ValueError, KeyError):
                continue
    todo = [u for u in urls if u not in done]
    print(f"unique sites: {len(urls)}, cached: {len(done)}, todo: {len(todo)}")

    # retry network errors (status -1) from previous runs
    if "-1" in sys.argv and CACHE.exists():
        keep = []
        for line in CACHE.read_text().splitlines():
            try:
                if json.loads(line).get("status") != -1:
                    keep.append(line)
            except ValueError:
                keep.append(line)
        CACHE.write_text("\n".join(keep) + ("\n" if keep else ""))
        done = {json.loads(l)["url"] for l in keep}
        todo = [u for u in urls if u not in done]
        print(f"after dropping errors: todo {len(todo)}")

    if not todo:
        return 0

    t0 = time.time()
    n = 0
    with CACHE.open("a") as fh, cf.ThreadPoolExecutor(WORKERS) as ex:
        for rec in ex.map(scrape_one, todo, chunksize=8):
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            n += 1
            if n % 100 == 0:
                rate = n / (time.time() - t0 + 0.01)
                print(f"{n}/{len(todo)} ({rate:.1f}/s, eta {(len(todo)-n)/max(rate,0.01)/60:.0f}m)")
    print(f"done {n} in {(time.time()-t0)/60:.1f}m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
