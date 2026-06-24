""
prediction.py
Predicts when bins will become full and prioritizes collection.
"""

import pandas as pd

# A bin at or above this fill level is considered near/at overflow
OVERFLOW_THRESHOLD = 85

# Approximate daily fill-rate (% per day) by waste type, used to simulate
# how quickly each bin type typically fills up. These are illustrative
# defaults — swap in real sensor-derived rates if/when available.
_FILL_RATE_BY_TYPE = {
    "General Waste": 6.0,
    "Recyclable": 4.0,
    "Organic": 8.0,
    "E-waste": 1.5,
    "Hazardous": 1.0,
}
_DEFAULT_FILL_RATE = 5.0


def _estimate_days_to_full(fill_level: float, waste_type: str) -> float:
    """Estimate days until a bin reaches 100% fill, given its current level."""
    if fill_level >= 100:
        return 0.0
    rate = _FILL_RATE_BY_TYPE.get(waste_type, _DEFAULT_FILL_RATE)
    remaining = 100 - fill_level
    days = remaining / rate
    return round(days, 1)


def _urgency_for(fill_level: float, days_to_full: float) -> str:
    if fill_level >= OVERFLOW_THRESHOLD or days_to_full <= 1:
        return "CRITICAL"
    elif days_to_full <= 2:
        return "HIGH"
    elif days_to_full <= 4:
        return "MEDIUM"
    else:
        return "LOW"


def _message_for(bin_id: str, fill_level: float, days_to_full: float, urgency: str) -> str:
    if urgency == "CRITICAL":
        return f"Currently {fill_level}% full — collect immediately to avoid overflow."
    elif urgency == "HIGH":
        return f"At {fill_level}% full, expected to fill in ~{days_to_full} day(s) — schedule pickup soon."
    elif urgency == "MEDIUM":
        return f"At {fill_level}% full, expected to fill in ~{days_to_full} days — plan for upcoming collection."
    else:
        return f"At {fill_level}% full, expected to fill in ~{days_to_full} days — no action needed yet."


def get_priority_collection_list(bins_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame of bins (bin_id, location, waste_type, fill_level, ...),
    return a prioritized DataFrame with predicted days_to_full, urgency, and
    a human-readable message, sorted most-urgent first.
    """
    records = []
    for _, row in bins_df.iterrows():
        fill_level = float(row["fill_level"])
        waste_type = row["waste_type"]
        days_to_full = _estimate_days_to_full(fill_level, waste_type)
        urgency = _urgency_for(fill_level, days_to_full)
        message = _message_for(row["bin_id"], fill_level, days_to_full, urgency)

        records.append({
            "bin_id": row["bin_id"],
            "location": row["location"],
            "waste_type": waste_type,
            "fill_level": fill_level,
            "days_to_full": days_to_full,
            "urgency": urgency,
            "message": message,
        })

    result_df = pd.DataFrame(records)

    urgency_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    result_df["_sort_key"] = result_df["urgency"].map(urgency_order)
    result_df = result_df.sort_values(["_sort_key", "days_to_full"]).drop(columns="_sort_key")
    result_df = result_df.reset_index(drop=True)

    return result_df
