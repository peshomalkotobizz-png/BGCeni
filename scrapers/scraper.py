"""
ЦениBG — РЕАЛЕН Scraper
Playwright за JS сайтове (Kaufland, Billa), requests за Lidl.
Стартирай веднъж: python -m playwright install chromium
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "bg-BG,bg;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EMOJI_MAP = {
    "мляко": "🥛", "кисело": "🫙", "масло": "🧈", "яйц": "🥚",
    "хляб": "🍞", "захар": "🍬", "кафе": "☕", "шоколад": "🍫",
    "банан": "🍌", "домат": "🍅", "зехтин": "🫒", "прах": "🧺",
    "шампо": "🧴", "препарат": "🫧", "тоалет": "🧻", "пиле": "🍗",
    "кайма": "🥩", "месо": "🥩", "риба": "🐟", "сирен": "🧀",
    "сок": "🥤", "вода": "💧", "бира": "🍺", "вино": "🍷",
    "чай": "🍵", "ориз": "🍚", "паста": "🍝",
}

def get_emoji(name: str) -> str:
    n = name.lower()
    for kw, em in EMOJI_MAP.items():
        if kw in n:
            return em
    return "🛒"

def parse_price(text: str):
    if not text:
        return None
    cleaned = re.sub(r"[^\d,.]", "", text.replace(",", "."))
    m = re.search(r"\d+\.?\d*", cleaned)
    try:
        v = float(m.group()) if m else None
        return v if v and 0.01 < v < 5000 else None
    except Exception:
        return None

def delay(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


# ══════════════════════════════════════════════════════════════
# LIDL — requests + BeautifulSoup
# ══════════════════════════════════════════════════════════════
LIDL_URLS = [
    "https://www.lidl.bg/p/mlqchni-produkti/c/1200",
    "https://www.lidl.bg/p/mesni-produkti/c/1300",
    "https://www.lidl.bg/p/hlyab-i-pekarni-produkti/c/1400",
    "https://www.lidl.bg/p/pijalni/c/1500",
    "https://www.lidl.bg/p/domakinska-himiqsq/c/4100",
]

def scrape_lidl_real():
    products = []
    sess = requests.Session()
    sess.headers.update(HEADERS)

    for url in LIDL_URLS:
        try:
            print(f"  [Lidl] {url}")
            r = sess.get(url, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")

            # Опитай различни CSS селектори — Lidl понякога ги сменя
            cards = (
                soup.select("[class*='product-grid-box']") or
                soup.select("[class*='product-tile']") or
                soup.select("[class*='s-product-detail']")
            )

            for card in cards[:15]:
                name_el = (
                    card.select_one("[class*='description']") or
                    card.select_one("[class*='product__title']") or
                    card.select_one("h3")
                )
                price_el = (
                    card.select_one("[class*='m-price__price']") or
                    card.select_one("[class*='price__integer']") or
                    card.select_one("[class*='price']")
                )
                if not name_el or not price_el:
                    continue
                name = name_el.get_text(strip=True)
                price = parse_price(price_el.get_text())
                if name and price:
                    products.append({"store": "Lidl", "name": name[:150], "emoji": get_emoji(name), "price": price})

            delay(1.5, 3.0)
        except Exception as e:
            print(f"  [Lidl ERR] {e}")

    print(f"  [Lidl] {len(products)} продукта")
    return products


# ══════════════════════════════════════════════════════════════
# KAUFLAND — Playwright
# ══════════════════════════════════════════════════════════════
KAUFLAND_URLS = [
    "https://www.kaufland.bg/produkti/mlechni-produkti-i-yaytsa.html",
    "https://www.kaufland.bg/produkti/meso-i-ribni-produkti.html",
    "https://www.kaufland.bg/produkti/hlyab-i-testo.html",
    "https://www.kaufland.bg/produkti/napitki.html",
    "https://www.kaufland.bg/produkti/domakinski-potrebnosti.html",
]

def scrape_kaufland_real():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [Kaufland] pip install playwright && python -m playwright install chromium")
        return []

    products = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(user_agent=HEADERS["User-Agent"], locale="bg-BG")
        page = ctx.new_page()

        for url in KAUFLAND_URLS:
            try:
                print(f"  [Kaufland] {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)
                try:
                    page.wait_for_selector("[class*='product-tile'], [class*='c-product']", timeout=8000)
                except Exception:
                    pass

                # Scroll за lazy-load
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    page.wait_for_timeout(700)

                soup = BeautifulSoup(page.content(), "html.parser")
                cards = (
                    soup.select("[class*='product-tile']") or
                    soup.select("[class*='c-product-tile']") or
                    soup.select("[class*='c-product']")
                )

                for card in cards[:15]:
                    name_el = (
                        card.select_one("[class*='product-tile__name']") or
                        card.select_one("[class*='product__name']") or
                        card.select_one("[class*='title']")
                    )
                    price_el = (
                        card.select_one("[class*='price__unit']") or
                        card.select_one("[class*='price__integer']") or
                        card.select_one("[class*='price']")
                    )
                    if not name_el or not price_el:
                        continue
                    name = name_el.get_text(strip=True)
                    price = parse_price(price_el.get_text())
                    if name and price:
                        products.append({"store": "Kaufland", "name": name[:150], "emoji": get_emoji(name), "price": price})

                delay(2.0, 4.0)
            except Exception as e:
                print(f"  [Kaufland ERR] {e}")

        browser.close()

    print(f"  [Kaufland] {len(products)} продукта")
    return products


# ══════════════════════════════════════════════════════════════
# BILLA — опит за API, после Playwright
# ══════════════════════════════════════════════════════════════
BILLA_URLS = [
    "https://www.billa.bg/kategorii/mlechni-produkti-i-yaitsa",
    "https://www.billa.bg/kategorii/meso-i-riba",
    "https://www.billa.bg/kategorii/hlyab-i-testo",
    "https://www.billa.bg/kategorii/napitki",
    "https://www.billa.bg/kategorii/domakinska-himiya",
]

def scrape_billa_real():
    # 1. Опит за JSON API
    for api in [
        "https://www.billa.bg/api/products?category=dairy&limit=50",
        "https://www.billa.bg/api/v1/products?size=50",
    ]:
        try:
            r = requests.get(api, headers={**HEADERS, "Accept": "application/json"}, timeout=8)
            if r.status_code == 200 and "json" in r.headers.get("Content-Type", ""):
                data = r.json()
                items = data.get("products", data.get("hits", data if isinstance(data, list) else []))
                if items:
                    result = []
                    for item in items[:60]:
                        name = item.get("name", item.get("title", ""))
                        pr = item.get("price", {})
                        price = pr.get("amount", pr.get("value", pr)) if isinstance(pr, dict) else pr
                        if name and price:
                            result.append({"store": "Billa", "name": str(name)[:150], "emoji": get_emoji(str(name)), "price": float(price)})
                    if result:
                        print(f"  [Billa] API: {len(result)} продукта")
                        return result
        except Exception:
            pass

    # 2. Playwright + XHR прихващане
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [Billa] pip install playwright && python -m playwright install chromium")
        return []

    products = []
    captured = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=HEADERS["User-Agent"], locale="bg-BG")
        page = ctx.new_page()

        def on_response(resp):
            if "api" in resp.url and resp.status == 200:
                try:
                    if "json" in resp.headers.get("content-type", ""):
                        data = resp.json()
                        items = data.get("products", data.get("hits", []))
                        for it in items:
                            n = it.get("name", it.get("title", ""))
                            pr = it.get("price", {})
                            price = pr.get("amount", pr.get("value", pr)) if isinstance(pr, dict) else pr
                            if n and price:
                                captured.append({"store": "Billa", "name": str(n)[:150], "emoji": get_emoji(str(n)), "price": float(price)})
                except Exception:
                    pass

        page.on("response", on_response)

        for url in BILLA_URLS[:3]:
            try:
                print(f"  [Billa] {url}")
                page.goto(url, wait_until="networkidle", timeout=35000)
                page.wait_for_timeout(2000)

                if captured:
                    products.extend(captured[:15])
                    captured.clear()
                    delay(1.5, 3.0)
                    continue

                # HTML парсиране
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    page.wait_for_timeout(700)

                soup = BeautifulSoup(page.content(), "html.parser")
                cards = soup.select("[class*='product-tile'], [class*='product-card'], [class*='c-product']")

                for card in cards[:15]:
                    name_el = card.select_one("[class*='name']") or card.select_one("[class*='title']") or card.select_one("h3")
                    price_el = card.select_one("[class*='price']")
                    if not name_el or not price_el:
                        continue
                    name = name_el.get_text(strip=True)
                    price = parse_price(price_el.get_text())
                    if name and price:
                        products.append({"store": "Billa", "name": name[:150], "emoji": get_emoji(name), "price": price})

                delay(2.0, 4.0)
            except Exception as e:
                print(f"  [Billa ERR] {e}")

        browser.close()

    print(f"  [Billa] {len(products)} продукта")
    return products


# ══════════════════════════════════════════════════════════════
# ГЛАВНА ФУНКЦИЯ
# ══════════════════════════════════════════════════════════════
def run_all_scrapers(app):
    with app.app_context():
        from database import db, Product, PriceHistory

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ═══ Scraping старт ═══")
        t0 = time.time()

        all_products = []
        for fn, label in [(scrape_lidl_real, "Lidl"), (scrape_kaufland_real, "Kaufland"), (scrape_billa_real, "Billa")]:
            print(f"\n→ {label}")
            try:
                all_products += fn()
            except Exception as e:
                print(f"  [{label} FATAL] {e}")

        updated = new_count = 0
        for item in all_products:
            if not item.get("name") or not item.get("price"):
                continue
            product = Product.query.filter_by(name=item["name"], store=item["store"]).first()
            if not product:
                product = Product(name=item["name"], emoji=item.get("emoji","🛒"), store=item["store"], current_price=item["price"])
                db.session.add(product)
                db.session.flush()
                new_count += 1
            else:
                product.current_price = item["price"]
            product.last_scraped = datetime.utcnow()

            today_entry = PriceHistory.query.filter(
                PriceHistory.product_id == product.id,
                db.func.date(PriceHistory.date) == date.today()
            ).first()
            if not today_entry:
                db.session.add(PriceHistory(product_id=product.id, price=item["price"], date=datetime.utcnow()))
            updated += 1

        db.session.commit()
        print(f"\n✓ {updated} обновени ({new_count} нови) за {time.time()-t0:.1f}с\n")
        return updated


if __name__ == "__main__":
    print("Тест на scraper-а (без база)...\n")
    for fn, label in [(scrape_lidl_real,"LIDL"),(scrape_kaufland_real,"KAUFLAND"),(scrape_billa_real,"BILLA")]:
        print(f"\n=== {label} ===")
        for p in fn()[:5]:
            print(f"  {p['emoji']} {p['name']} — {p['price']:.2f} лв.")
