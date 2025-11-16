import os
import csv
import time
import re
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

LEADS_CSV = os.path.join(DATA_DIR, "leads.csv")

load_dotenv()
PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


def google_places_search(query, location="35.6762,139.6503", radius_m=5000, max_results=30):
    """
    Uses official Google Places Text Search API.
    query: 'restaurant', 'dentist in Kobe', etc.
    location: 'lat,lng' (Tokyo by default)
    radius_m: search radius in meters
    max_results: cap number of places
    """
    if not PLACES_API_KEY:
        raise RuntimeError("GOOGLE_PLACES_API_KEY not set in .env")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "radius": radius_m,
        "key": PLACES_API_KEY,
    }

    places = []
    next_page_token = None

    while True:
        if next_page_token:
            params["pagetoken"] = next_page_token
            # Google requires a short delay before using next_page_token
            time.sleep(2)

        full_url = f"{url}?{urlencode(params)}"
        print("🔍 Fetching:", full_url)

        resp = requests.get(full_url)
        data = resp.json()
        results = data.get("results", [])
        places.extend(results)

        if len(places) >= max_results:
            places = places[:max_results]
            break

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

    print(f"✅ Found {len(places)} places from Google.")
    return places


def get_place_details(place_id):
    """
    Fetch extra details (website, phone) for a Place ID.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website,formatted_phone_number",
        "key": PLACES_API_KEY,
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    return data.get("result", {})


EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")


def extract_email_from_website(url, timeout=8):
    """
    Fetch homepage HTML and try to find an email address.
    """
    if not url:
        return None

    try:
        print(f"🌐 Checking website for email: {url}")
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code}")
            return None

        html = resp.text
        emails = EMAIL_REGEX.findall(html)
        if not emails:
            print("  ℹ️ No email found on page.")
            return None

        # Basic filter: avoid obviously invalid or Google emails, etc.
        cleaned = []
        for e in emails:
            e_low = e.lower()
            if "example.com" in e_low:
                continue
            if "@gmail" in e_low or "@yahoo" in e_low or "@hotmail" in e_low:
                # still acceptable for small businesses, include
                cleaned.append(e)
            else:
                cleaned.append(e)
        if not cleaned:
            print("  ℹ️ Only dummy emails detected.")
            return None

        email = cleaned[0]
        print(f"  ✅ Found email: {email}")
        return email

    except Exception as e:
        print(f"  ❌ Error fetching website {url}: {e}")
        return None


def parse_city_from_address(address):
    """
    Very rough city extraction from formatted address.
    For Japan: address often contains prefecture + city.
    We'll just return everything before the last comma or the full string.
    """
    if not address:
        return ""
    if "," in address:
        return address.split(",")[-2].strip()
    return address


def append_leads_to_csv(leads):
    """
    Append new leads to data/leads.csv.
    Format: business_name,industry,city,email
    """
    file_exists = os.path.exists(LEADS_CSV)

    with open(LEADS_CSV, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["business_name", "industry", "city", "email"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for lead in leads:
            writer.writerow(lead)

    print(f"💾 Saved {len(leads)} leads → {LEADS_CSV}")


def run_google_scraper(
    query="restaurant in Kobe",
    location="34.6901,135.1955",  # Kobe center
    radius_m=5000,
    max_results=15,
    industry_label="restaurant",
):
    """
    Main entry point: search Google Places, enrich with website/email,
    and append to leads.csv for your leads engine.
    """
    places = google_places_search(query, location, radius_m, max_results)
    leads = []

    for p in places:
        name = p.get("name", "").strip()
        address = p.get("formatted_address", "").strip()
        city = parse_city_from_address(address)

        place_id = p.get("place_id")
        details = get_place_details(place_id) if place_id else {}
        website = details.get("website", "")

        email = extract_email_from_website(website) if website else None

        # If no email, skip for now (you can change this later)
        if not email:
            continue

        lead = {
            "business_name": name,
            "industry": industry_label,
            "city": city or "Global",
            "email": email,
        }
        print(f"➡ Lead: {lead}")
        leads.append(lead)

        # Gentle delay between websites (avoid hammering sites)
        time.sleep(1.0)

    if not leads:
        print("⚠️ No leads with emails were found. You may need a different query or city.")
        return

    append_leads_to_csv(leads)


if __name__ == "__main__":
    # Example: restaurants in Kobe
    run_google_scraper(
        query="restaurant in Kobe",
        location="34.6901,135.1955",
        radius_m=6000,
        max_results=15,
        industry_label="restaurant",
    )
