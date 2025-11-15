
import asyncio
import argparse
import logging
import re
from pathlib import Path
import pandas as pd
from playwright.async_api import async_playwright

try:
    from .delivery import send_report
except Exception:
    def send_report(*args, **kwargs):
        print("[delivery] (stub) Not available")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("cli")

DATA_DIR = Path("data/leads")
DATA_DIR.mkdir(parents=True, exist_ok=True)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
RESULT_CARD_SEL = "div[role='article'], div.Nv2PK"
FEED_SEL = "div[role='feed']"
NAME_SEL_DETAIL = "h1.DUwDvf, h1[aria-level='1']"
ADDR_BTN = "button[data-item-id*='address']"
PHONE_BTN = "button[data-item-id*='phone']"
WEBSITE_BTN = "a[data-item-id*='authority'], a[aria-label^='Website']"
CONSENT_BTNS = [
    "button:has-text('I agree')",
    "button:has-text('Accept all')",
    "button:has-text('Accept')",
    "button:has-text('Got it')",
]

async def _maybe_click(page, selector, timeout=2000):
    try:
        await page.locator(selector).first.wait_for(timeout=timeout)
        await page.locator(selector).first.click()
        return True
    except:
        return False

async def _maybe_text(page, selector, attr=None):
    try:
        loc = page.locator(selector).first
        await loc.wait_for(timeout=2000)
        if attr:
            v = await loc.get_attribute(attr)
            return v or ""
        return (await loc.inner_text()).strip()
    except:
        return ""

async def _feed_scroll(page, steps=14, per_step=2400):
    try:
        feed = page.locator(FEED_SEL)
        await feed.wait_for(timeout=12000)
        for _ in range(steps):
            await page.evaluate("(el, y) => el.scrollBy(0, y)", await feed.element_handle(), per_step)
            await asyncio.sleep(0.8)
        return True
    except:
        return False

async def gmaps_search(niche: str, city: str, country: str, rows: int = 50):
    query = f"{niche} in {city}, {country}"
    log.info(f"Searching for: {query}")
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(locale="en-US")
        page = await ctx.new_page()

        url = "https://www.google.com/maps/search/" + re.sub(r"\s+", "+", f"{niche} {city} {country}") + "?hl=en&gl=us"
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")

        for b in CONSENT_BTNS:
            if await _maybe_click(page, b, timeout=2000):
                break

        try:
            await page.locator(FEED_SEL).wait_for(timeout=12000)
        except:
            pass

        await _feed_scroll(page, steps=18, per_step=2600)

        cards = page.locator(RESULT_CARD_SEL)
        count = await cards.count()
        if count == 0:
            await asyncio.sleep(3)
            await _feed_scroll(page, steps=10, per_step=2600)
            count = await cards.count()
        log.info(f"Found {count} cards")

        max_i = min(rows, count)
        for i in range(max_i):
            try:
                item = cards.nth(i)
                await item.scroll_into_view_if_needed(timeout=5000)
                await item.click()
                await asyncio.sleep(1.3)

                name = await _maybe_text(page, NAME_SEL_DETAIL)
                address = await _maybe_text(page, ADDR_BTN)
                phone = await _maybe_text(page, PHONE_BTN)
                website_href = await _maybe_text(page, WEBSITE_BTN, attr="href")

                email = ""
                if website_href:
                    try:
                        sub = await ctx.new_page()
                        await sub.goto(website_href, timeout=15000, wait_until="domcontentloaded")
                        html = await sub.content()
                        m = EMAIL_RE.search(html)
                        if m: email = m.group(0)
                        await sub.close()
                    except:
                        pass

                if name:
                    results.append({
                        "Business Name": name,
                        "Address": address,
                        "Phone": phone,
                        "Website": website_href or "",
                        "Email": email,
                        "City": city,
                        "Country": country,
                        "Niche": niche,
                    })
            except Exception as e:
                log.warning(f"Card {i} error: {e}")
                continue

        await browser.close()
    return results

def save_results(niche: str, city: str, country: str, leads: list):
    if not leads:
        log.warning("⚠️ No leads found.")
        return None
    df = pd.DataFrame(leads)
    out = DATA_DIR / f"{niche}_{city}_{country}.xlsx".replace(" ", "_")
    df.to_excel(out, index=False)
    log.info(f"✅ Saved {len(leads)} leads → {out}")
    return out

async def main():
    ap = argparse.ArgumentParser(description="Web automation lead scraper")
    ap.add_argument("--niche", required=True)
    ap.add_argument("--city", required=True)
    ap.add_argument("--country", default="USA")
    ap.add_argument("--rows", type=int, default=50)
    ap.add_argument("--email", action="store_true", help="send the Excel via email using config.yaml")
    args = ap.parse_args()

    leads = await gmaps_search(args.niche, args.city, args.country, args.rows)
    out = save_results(args.niche, args.city, args.country, leads)
    if out and args.email:
        send_report(out)

if __name__ == "__main__":
    asyncio.run(main())
