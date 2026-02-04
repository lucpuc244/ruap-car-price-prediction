import os
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# =========================
# POSTAVKE
# =========================
START_URL = "https://www.njuskalo.hr/rabljeni-auti?geo%5BlocationIds%5D=1160%2C1168%2C1161%2C1151"
START_PAGE = 1

MAX_LISTINGS = 5000
MIN_PRICE = 500

AUTOSAVE_EVERY = 50
MIN_SLEEP = 2.5
MAX_SLEEP = 5.0

OUT_CSV = "njuskalo_osijek_regija_auti_5000.csv"
OUT_XLSX = "njuskalo_osijek_regija_auti_5000.xlsx"

# Target + Features (BEZ goriva i BEZ potrošnje)
COLUMNS = [
    "Price_market",  # target
    "Age",
    "Mileage",
    "Brand",
    "Model",
    "Power_kW",
    "Transmission",
    "url",
    "title",
]

# HR label -> internal key
LABEL_MAP = {
    "Marka automobila": "brand",
    "Model automobila": "model",
    "Tip automobila": "trim",
    "Godina proizvodnje": "year",
    "Prijeđeni kilometri": "mileage_km",
    "Snaga motora": "power_kw",
    "Mjenjač": "transmission",
}

NUMERIC_KEYS = {"year", "mileage_km", "power_kw"}


# =========================
# HELPERI
# =========================
def sleep_polite():
    time.sleep(random.uniform(MIN_SLEEP, MAX_SLEEP))


def to_int(s):
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", str(s))
    return int(digits) if digits else None


def extract_price_eur(text: str):
    # hvata "19.900 €" i slično
    m = re.search(r"([\d\.\s]+)\s*€", text)
    if not m:
        return None
    return to_int(m.group(1))


def is_captcha(page_text: str, page_url: str) -> bool:
    u = (page_url or "").lower()
    t = (page_text or "").lower()
    return ("captcha" in u) or ("unblock" in u) or ("captcha" in t)


def wait_user_if_captcha(page):
    try:
        body_text = page.inner_text("body", timeout=8000) or ""
    except Exception:
        body_text = ""
    if is_captcha(body_text, page.url):
        print("\n⚠ CAPTCHA / blokada detektirana.")
        print("   Riješi CAPTCHA u browser prozoru.")
        input("   Kad riješiš, stisni ENTER u CMD-u za nastavak...")


def safe_goto(page, url, timeout_ms=90000, wait_until="domcontentloaded"):
    try:
        page.goto(url, wait_until=wait_until, timeout=timeout_ms)
        return True
    except PWTimeoutError:
        return False
    except Exception:
        return False


def collect_listing_links(page):
    links = set()
    try:
        for a in page.query_selector_all("a[href]"):
            href = a.get_attribute("href")
            if not href:
                continue
            full = urljoin(page.url, href)
            path = urlparse(full).path.lower()
            if "/auti/" in path:
                links.add(full)
    except Exception:
        pass
    return sorted(links)


def parse_label_value_pairs(page):
    pairs = {}

    # 1) tablica label/value
    try:
        for tr in page.query_selector_all("tr"):
            tds = tr.query_selector_all("td")
            if len(tds) == 2:
                label = (tds[0].inner_text() or "").strip()
                value = (tds[1].inner_text() or "").strip()
                if label and value:
                    pairs[label] = value
    except Exception:
        pass

    # 2) fallback regex iz body teksta
    if not pairs:
        try:
            text = page.inner_text("body") or ""
        except Exception:
            text = ""
        for hr_label in LABEL_MAP.keys():
            m = re.search(
                rf"{re.escape(hr_label)}\s*[:\n]\s*([^\n]+)",
                text,
                flags=re.IGNORECASE
            )
            if m:
                pairs[hr_label] = m.group(1).strip()

    return pairs


def autosave_csv(rows):
    df = pd.DataFrame(rows)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[COLUMNS].drop_duplicates(subset=["url"]).reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(f"💾 Autosave: {len(df)} spremljeno -> {OUT_CSV}")


def finalize_excel():
    df = pd.read_csv(OUT_CSV, encoding="utf-8")
    df.to_excel(OUT_XLSX, index=False)
    print(f"📗 Excel spremljen -> {OUT_XLSX}")


def build_row(page, url):
    # otvori oglas
    if not safe_goto(page, url, timeout_ms=120000):
        return None

    wait_user_if_captcha(page)

    # pročitaj body + title
    try:
        body = page.inner_text("body") or ""
    except Exception:
        return None

    h1 = page.query_selector("h1")
    title = (h1.inner_text() or "").strip() if h1 else ""

    price = extract_price_eur(body)
    if price is None or price < MIN_PRICE:
        return None

    pairs = parse_label_value_pairs(page)

    raw = {}
    for hr_label, key in LABEL_MAP.items():
        if hr_label in pairs and pairs[hr_label]:
            val = pairs[hr_label]
            raw[key] = to_int(val) if key in NUMERIC_KEYS else val

    brand = raw.get("brand")
    model = raw.get("model") or raw.get("trim")
    year = raw.get("year")
    mileage = raw.get("mileage_km")
    power_kw = raw.get("power_kw")
    transmission = raw.get("transmission")

    # preskoči ako fali bilo koji od traženih parametara
    if not brand or not model:
        return None
    if year is None or mileage is None or power_kw is None:
        return None
    if not transmission:
        return None

    age = datetime.now().year - int(year)

    return {
        "Price_market": price,
        "Age": age,
        "Mileage": int(mileage),
        "Brand": brand,
        "Model": model,
        "Power_kW": int(power_kw),
        "Transmission": transmission,
        "url": url,
        "title": title,
    }


# =========================
# MAIN
# =========================
def main():
    rows = []
    seen = set()

    # resume ako već postoji CSV
    if os.path.exists(OUT_CSV):
        try:
            df_old = pd.read_csv(OUT_CSV, encoding="utf-8")
            rows = df_old.to_dict("records")
            if "url" in df_old.columns:
                seen = set(df_old["url"].dropna().astype(str).tolist())
            print(f"📂 Resume: učitano {len(rows)} redova iz {OUT_CSV}")
        except Exception:
            print("⚠ Ne mogu učitati postojeći CSV, krećem ispočetka.")
            rows, seen = [], set()

    if len(rows) >= MAX_LISTINGS:
        print(f"✅ Već imaš {len(rows)} (cilj {MAX_LISTINGS}).")
        finalize_excel()
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page_no = START_PAGE
        attempt_no = 0

        while len(rows) < MAX_LISTINGS:
            list_url = f"{START_URL}&page={page_no}"
            print(f"\n📄 List stranica {page_no} | spremljeno {len(rows)}/{MAX_LISTINGS}")
            print(f"   {list_url}")

            ok = safe_goto(page, list_url, timeout_ms=90000)
            if not ok:
                print("⏭ Timeout na list stranici, idem dalje...")
                page_no += 1
                continue

            wait_user_if_captcha(page)

            links = collect_listing_links(page)
            print(f"🔗 Linkova na stranici: {len(links)}")

            if not links:
                print("⚠ Nema linkova (kraj rezultata ili blokada).")
                break

            new_links = 0
            for link in links:
                if len(rows) >= MAX_LISTINGS:
                    break
                if link in seen:
                    continue

                seen.add(link)
                new_links += 1
                attempt_no += 1

                print(f"🚗 Pokušaj #{attempt_no} | spremljeno {len(rows)}")

                sleep_polite()
                item = build_row(page, link)
                if item:
                    rows.append(item)
                    print(f"✅ SPREMLJENO: {len(rows)}/{MAX_LISTINGS} | Price={item['Price_market']}€")

                    if len(rows) % AUTOSAVE_EVERY == 0:
                        autosave_csv(rows)

            if new_links == 0:
                print("⚠ Nema novih linkova, prekid.")
                break

            page_no += 1

        autosave_csv(rows)
        context.close()
        browser.close()

    finalize_excel()
    print(f"\n🎉 GOTOVO – {len(rows)} redova (>=500€) spremljeno u CSV i Excel.")


if __name__ == "__main__":
    main()
