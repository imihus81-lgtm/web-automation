import json
import os
import random
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

STATS_FILE = os.path.join(DATA_DIR, "brain_stats.json")

# Global pools so the brain always has something to explore
GLOBAL_NICHES = [
    "restaurant",
    "cafe",
    "auto repair",
    "car dealer",
    "clinic",
    "dentist",
    "salon",
    "barber",
    "spa",
    "real estate",
    "roofing",
    "cleaning",
    "fitness",
    "law firm",
    "photography",
    "ecommerce",
    "coffee shop",
    "pet grooming",
    "accounting",
]

GLOBAL_COUNTRIES = [
    "Japan",
    "USA",
    "UK",
    "Canada",
    "Australia",
    "Germany",
    "France",
    "UAE",
    "Singapore",
    "India",
]

DEFAULT_STATS = {
    "niches": {},
    "countries": {},
    "subjects": {},
    "total_sent": 0,
    "total_opens": 0,
    "total_clicks": 0,
    "total_conversions": 0,
    "last_updated": None,
}


def load_stats():
    """Load brain stats from disk or create default structure."""
    if not os.path.exists(STATS_FILE):
        save_stats(DEFAULT_STATS)
        return DEFAULT_STATS.copy()

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = DEFAULT_STATS.copy()

    # Ensure all keys exist
    for k, v in DEFAULT_STATS.items():
        if k not in data:
            data[k] = v

    return data


def save_stats(data):
    """Persist brain stats to disk."""
    data["last_updated"] = str(datetime.now())
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def record_result(niche, country, subject, opened=False, clicked=False, converted=False):
    """
    Update stats after sending an email.

    For now leads_engine_v6 calls this with all False (no tracking yet),
    but the structure is ready for future:
      - opened=True
      - clicked=True
      - converted=True
    """
    stats = load_stats()

    stats["total_sent"] += 1
    if opened:
        stats["total_opens"] += 1
    if clicked:
        stats["total_clicks"] += 1
    if converted:
        stats["total_conversions"] += 1

    if niche not in stats["niches"]:
        stats["niches"][niche] = {"sent": 0, "opens": 0, "clicks": 0, "conversions": 0}
    if country not in stats["countries"]:
        stats["countries"][country] = {"sent": 0, "opens": 0, "clicks": 0, "conversions": 0}
    if subject not in stats["subjects"]:
        stats["subjects"][subject] = {"sent": 0, "opens": 0, "clicks": 0, "conversions": 0}

    stats["niches"][niche]["sent"] += 1
    stats["countries"][country]["sent"] += 1
    stats["subjects"][subject]["sent"] += 1

    if opened:
        stats["niches"][niche]["opens"] += 1
        stats["countries"][country]["opens"] += 1
        stats["subjects"][subject]["opens"] += 1

    if clicked:
        stats["niches"][niche]["clicks"] += 1
        stats["countries"][country]["clicks"] += 1
        stats["subjects"][subject]["clicks"] += 1

    if converted:
        stats["niches"][niche]["conversions"] += 1
        stats["countries"][country]["conversions"] += 1
        stats["subjects"][subject]["conversions"] += 1

    save_stats(stats)


def _score_bucket(bucket_entry):
    """
    Compute a 'power score' for a niche/country/subject entry.
    Score combines conversions, clicks, opens (per sent), with smoothing.
    """
    sent = bucket_entry.get("sent", 0)
    opens = bucket_entry.get("opens", 0)
    clicks = bucket_entry.get("clicks", 0)
    conv = bucket_entry.get("conversions", 0)

    if sent == 0:
        return 0.0

    # Weighted signal
    raw_score = (conv * 10.0) + (clicks * 3.0) + (opens * 1.0)
    return raw_score / sent


def choose_best_niche(epsilon: float = 0.2) -> str:
    """
    Brain V7:
      - 20% of the time: explore a random global niche
      - 80% of the time: exploit the best-performing recorded niche
    """
    stats = load_stats()

    # Exploration
    if random.random() < epsilon or not stats["niches"]:
        return random.choice(GLOBAL_NICHES)

    # Exploitation: select niche with highest score
    best_niche = None
    best_score = -1.0

    for niche, data in stats["niches"].items():
        score = _score_bucket(data)
        # small random noise so ties don't always pick same
        score += random.random() * 0.01
        if score > best_score:
            best_score = score
            best_niche = niche

    return best_niche or random.choice(GLOBAL_NICHES)


def choose_best_country(epsilon: float = 0.25) -> str:
    """
    Brain V7:
      - 25% of the time: explore a random global country
      - 75% of the time: exploit the best-performing country
    """
    stats = load_stats()

    if random.random() < epsilon or not stats["countries"]:
        return random.choice(GLOBAL_COUNTRIES)

    best_country = None
    best_score = -1.0

    for c, data in stats["countries"].items():
        score = _score_bucket(data)
        score += random.random() * 0.01
        if score > best_score:
            best_score = score
            best_country = c

    return best_country or random.choice(GLOBAL_COUNTRIES)


def choose_subject():
    """
    Choose email subject with softmax-like weighting based on opens.
    If no history → random baseline subject.
    """
    stats = load_stats()

    base_subjects = [
        "We built a website for your business",
        "Your new website preview is ready",
        "Website proposal for your company",
        "Exclusive AI website demo for you",
        "Your business now has an AI website",
    ]

    # If no subjects tracked yet, randomly choose from base list
    if not stats["subjects"]:
        return random.choice(base_subjects)

    # Ensure tracked subjects always include the base ones
    for subj in base_subjects:
        if subj not in stats["subjects"]:
            stats["subjects"][subj] = {"sent": 0, "opens": 0, "clicks": 0, "conversions": 0}
    save_stats(stats)

    # Build a weighted list based on opens
    weights = []
    subjects = []
    for subj, data in stats["subjects"].items():
        opens = data.get("opens", 0)
        sent = data.get("sent", 0)
        # simple "open rate" style signal + 1 to avoid zero
        weight = (opens + 1) / (sent + 1)
        subjects.append(subj)
        weights.append(weight)

    # Normalize weights
    total_w = sum(weights)
    if total_w <= 0:
        return random.choice(base_subjects)

    thresholds = []
    cumulative = 0.0
    for w in weights:
        cumulative += w / total_w
        thresholds.append(cumulative)

    r = random.random()
    for subj, thresh in zip(subjects, thresholds):
        if r <= thresh:
            return subj

    return subjects[-1]


def print_brain_summary():
    """
    Helper for debugging: print top niches/countries/subjects.
    You can call this manually in a separate script or REPL.
    """
    stats = load_stats()
    print("\n=== BRAIN SUMMARY ===")
    print("Total sent:", stats["total_sent"])
    print("Total opens:", stats["total_opens"])
    print("Total clicks:", stats["total_clicks"])
    print("Total conversions:", stats["total_conversions"])

    def top_entries(bucket, label, limit=5):
        print(f"\nTop {label}:")
        if not bucket:
            print("  (no data yet)")
            return
        ranked = sorted(
            bucket.items(),
            key=lambda kv: _score_bucket(kv[1]),
            reverse=True,
        )
        for name, data in ranked[:limit]:
            print(
                f"  {name}: sent={data['sent']} opens={data['opens']} "
                f"clicks={data['clicks']} conv={data['conversions']} "
                f"score={_score_bucket(data):.3f}"
            )

    top_entries(stats["niches"], "niches")
    top_entries(stats["countries"], "countries")
    top_entries(stats["subjects"], "subjects")
    print("======================\n")
