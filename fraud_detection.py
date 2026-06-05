"""
Défi — Détection de fraude financière.

Vous devez implémenter la fonction `detect_fraud`.
La fonction `load_transactions` vous est FOURNIE (ne la modifiez pas).
"""

import csv
from datetime import datetime, timezone
from collections import defaultdict
import math


def load_transactions(path):
    """Lit un fichier CSV de transactions et renvoie une liste de dicts."""
    transactions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            transactions.append(_clean_row(row))
    return transactions


def _clean_row(row):
    def get(key):
        v = row.get(key)
        return v.strip() if isinstance(v, str) and v.strip() != "" else None

    amount_raw = get("amount")
    try:
        amount = float(amount_raw) if amount_raw is not None else None
    except ValueError:
        amount = None

    card_raw = get("card_present")
    if card_raw is None:
        card_present = None
    else:
        card_present = card_raw.lower() in ("true", "1", "yes", "oui")

    return {
        "transaction_id": get("transaction_id"),
        "timestamp": get("timestamp"),
        "user_id": get("user_id"),
        "amount": amount,
        "currency": get("currency"),
        "merchant": get("merchant"),
        "country": get("country"),
        "card_present": card_present,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_ts(ts_str):
    """Parse ISO 8601 timestamp → datetime (UTC). Returns None on failure."""
    if not ts_str:
        return None
    try:
        # Handle trailing Z
        s = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


# Approximate distance between country centroids (degrees lat/lon).
# We only need to detect "impossibly fast" travel, so a rough heuristic
# based on known country centroids is enough.
_COUNTRY_CENTROIDS = {
    "FR": (46.2, 2.2), "DE": (51.2, 10.5), "GB": (55.4, -3.4),
    "ES": (40.5, -3.7), "IT": (41.9, 12.6), "BE": (50.5, 4.5),
    "NL": (52.1, 5.3), "PT": (39.4, -8.2), "CH": (46.8, 8.2),
    "AT": (47.5, 14.6), "PL": (52.1, 19.4), "SE": (60.1, 18.6),
    "NO": (60.5, 8.5), "DK": (56.3, 9.5), "FI": (61.9, 25.7),
    "US": (37.1, -95.7), "CA": (56.1, -106.3), "MX": (23.6, -102.5),
    "BR": (-14.2, -51.9), "AR": (-38.4, -63.6),
    "CN": (35.9, 104.2), "JP": (36.2, 138.3), "KR": (35.9, 127.8),
    "IN": (20.6, 78.9), "AU": (-25.3, 133.8),
    "ZA": (-30.6, 22.9), "NG": (9.1, 8.7), "EG": (26.8, 30.8),
    "MA": (31.8, -7.1), "CI": (7.5, -5.5), "SN": (14.5, -14.5),
    "TG": (8.6, 0.8), "GH": (7.9, -1.0), "CM": (3.9, 11.5),
    "RU": (61.5, 105.3), "TR": (38.9, 35.2), "SA": (23.9, 45.1),
    "AE": (23.4, 53.8), "IL": (31.0, 34.9), "SG": (1.4, 103.8),
    "TH": (15.9, 100.9), "MY": (4.2, 108.0), "ID": (-0.8, 113.9),
    "XOF": (12.0, -2.0),  # fallback for XOF currency code used as country
}


def _geo_distance_km(c1, c2):
    """Great-circle distance between two country codes (approximate km)."""
    if c1 not in _COUNTRY_CENTROIDS or c2 not in _COUNTRY_CENTROIDS:
        return None
    lat1, lon1 = _COUNTRY_CENTROIDS[c1]
    lat2, lon2 = _COUNTRY_CENTROIDS[c2]
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# Max speed (km/h) a human can plausibly travel between two transactions.
# Commercial flight ≈ 900 km/h; we add margin for connection times.
_MAX_TRAVEL_SPEED_KMH = 900.0


def _impossible_travel(ts1, country1, ts2, country2):
    """Return True if travel between two countries is physically implausible."""
    if not (ts1 and ts2 and country1 and country2):
        return False
    if country1 == country2:
        return False
    dist_km = _geo_distance_km(country1, country2)
    if dist_km is None:
        return False
    delta_h = abs((ts2 - ts1).total_seconds()) / 3600.0
    if delta_h < 0.01:  # essentially simultaneous → definitely impossible
        return delta_h == 0 or dist_km > 1
    required_speed = dist_km / delta_h
    return required_speed > _MAX_TRAVEL_SPEED_KMH


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_fraud(transactions):
    """Analyse une liste de transactions et renvoie un verdict pour chacune.

    Retour : list[dict] avec transaction_id, fraud_score (0-1),
    is_suspicious (bool), reason (str) — un résultat par transaction, même ordre.
    """
    # Parse timestamps once
    parsed = []
    for t in transactions:
        parsed.append({**t, "_ts": _parse_ts(t.get("timestamp"))})

    # Build per-user history sorted by timestamp (for context checks)
    user_txs = defaultdict(list)
    for t in parsed:
        uid = t.get("user_id")
        if uid:
            user_txs[uid].append(t)
    for uid in user_txs:
        user_txs[uid].sort(key=lambda x: (x["_ts"] or datetime.min.replace(tzinfo=timezone.utc)))

    results = []
    for t in parsed:
        tid = t.get("transaction_id")
        uid = t.get("user_id")
        amount = t.get("amount")
        country = t.get("country")
        ts = t["_ts"]

        reasons = []
        scores = []

        # ------------------------------------------------------------------
        # NIVEAU 1 — Anomalies évidentes
        # ------------------------------------------------------------------

        # Missing critical fields
        missing = []
        if amount is None:
            missing.append("amount")
        if not country:
            missing.append("country")
        if not t.get("currency"):
            missing.append("currency")
        if not t.get("merchant"):
            missing.append("merchant")

        if missing:
            reasons.append(f"Champs obligatoires manquants: {', '.join(missing)}")
            scores.append(0.85)

        # Negative or zero amount
        if amount is not None and amount <= 0:
            reasons.append("Montant nul ou négatif")
            scores.append(0.9)

        # ------------------------------------------------------------------
        # NIVEAU 2 — Logique métier (needs user history)
        # ------------------------------------------------------------------

        if uid:
            history = user_txs[uid]
            # Transactions of this user BEFORE the current one (excluding self)
            prior = [h for h in history
                     if h["transaction_id"] != tid
                     and h["_ts"] is not None
                     and (ts is None or h["_ts"] < ts)]

            # --- Montant anormal vs historique ---
            if amount is not None and amount > 0 and len(prior) >= 2:
                amounts = [h["amount"] for h in prior if h.get("amount") and h["amount"] > 0]
                if len(amounts) >= 2:
                    mean = sum(amounts) / len(amounts)
                    variance = sum((a - mean) ** 2 for a in amounts) / len(amounts)
                    std = math.sqrt(variance) if variance > 0 else 0
                    # Flag if amount > mean + 5*std AND > 3× mean
                    threshold_std = mean + max(5 * std, mean * 2)
                    if amount > threshold_std and amount > mean * 3:
                        factor = amount / mean
                        score = min(0.95, 0.7 + 0.05 * math.log(factor))
                        reasons.append("Montant très supérieur à l'habitude du client")
                        scores.append(score)

            # --- Fréquence suspecte (> 5 transactions in 10 minutes) ---
            if ts:
                recent = [h for h in prior
                          if h["_ts"] and abs((ts - h["_ts"]).total_seconds()) <= 600]
                if len(recent) >= 5:
                    reasons.append("Fréquence de transactions anormalement élevée")
                    scores.append(0.8)

            # --- Incohérence géographique (impossible travel) ---
            if ts and country:
                # Compare with all other user transactions within ±24 h
                nearby_time = [h for h in history
                               if h["transaction_id"] != tid
                               and h["_ts"] is not None
                               and h.get("country")
                               and abs((ts - h["_ts"]).total_seconds()) <= 86400]
                for other in nearby_time:
                    if _impossible_travel(ts, country, other["_ts"], other.get("country")):
                        reasons.append("Deux pays différents en trop peu de temps")
                        scores.append(0.88)
                        break  # one flag is enough

        # ------------------------------------------------------------------
        # Aggregate
        # ------------------------------------------------------------------
        if not reasons:
            # No red flags → clean transaction
            fraud_score = 0.0
            is_suspicious = False
            reason = "Transaction conforme au profil du client"
        else:
            # Take max score; deduplicate reasons
            seen = []
            for r in reasons:
                if r not in seen:
                    seen.append(r)
            fraud_score = round(max(scores), 4)
            is_suspicious = True
            reason = "; ".join(seen)

        results.append({
            "transaction_id": tid,
            "fraud_score": fraud_score,
            "is_suspicious": is_suspicious,
            "reason": reason,
        })

    return results