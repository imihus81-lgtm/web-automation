import os
import requests
import csv
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

OUTPUT_CSV = "data/leads_scraped.csv"
FIELDS = [
    "business_name",
    "category",
    "city",
    "email",
    "website",
    "phone",
    "address",
    "source",
]

os.makedirs("data", exist_ok=True)


def google_places_search(query, location="35.6762,139.6503", radius=50000):
    """
    query: 'restaurant', 'dentist', 'salon' etc
    location: 'lat,lng'
    radius: 50000 = 50km
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "key": API_KEY,
    }

    places = []
    next_page_token = None

    while True:
        if next_page_token:
            params["pagetoken"] = next_page_token

        full_url = f"{url}?{urlencode(params)}"
        print("Fetching:", full_url)

        resp = requests.get(full_url).json()
        places.extend(resp.get("results", []))

        next_page_token = resp.get("next_page_token")
        if not next_page_token:
            break

    return places


def extract_details(place):
    name = place.get("name", "")
    address = place.get("formatted_address", "")
    website = ""
    phone = ""

    # additional details request
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    details_params = {
        "place_id": place.get("place_id"),
        "fields": "website,formatted_phone_number",
        "key": API_KEY,
    }
    details = requests.get(details_url, params=details_params).json()

    result = details.get("result", {})
    website = result.get("website", "")
    phone = result.get("formatted_phone_number", "")

    return {
        "business_name": name,
        "category": place.get("types", [None])[0],
        "city": place.get("formatted_address", "").split(",")[-2].strip() if "," in address else "",
        "email": "",
        "website": website,
        "phone": phone,
        "address": address,
        "source": "google",
    }


def save_to_csv(rows):
    exists = os.path.exists(OUTPUT_CSV)

    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)


def run_google_scraper(niche="restaurant", location="35.6762,139.6503"):
    print(f"🔍 Scraping Google Places: {niche} near {location}")

    places = google_places_search(niche, location)
    print(f"Found {len(places)} places.")

    rows = []

    for p in places:
        details = extract_details(p)
        rows.append(details)

    save_to_csv(rows)
    print(f"Saved {len(rows)} leads → data/leads_scraped.csv")


if __name__ == "__main__":
    run_google_scraper("restaurant", "35.6762,139.6503")  # Tokyo
