"""
waste_classifier.py
Classifies a waste item into: Recyclable, Organic, E-waste, or Hazardous.
Uses a keyword-lookup dictionary (fast, no API cost). Falls back to a
"General Waste" category if no match is found.
"""

# Lookup dictionary: keyword -> category
WASTE_DB = {
    # Recyclable
    "plastic bottle": "Recyclable", "paper": "Recyclable", "newspaper": "Recyclable",
    "cardboard": "Recyclable", "glass bottle": "Recyclable", "tin can": "Recyclable",
    "aluminum can": "Recyclable", "plastic bag": "Recyclable", "magazine": "Recyclable",
    "carton": "Recyclable", "metal scrap": "Recyclable", "plastic container": "Recyclable",

    # Organic
    "food waste": "Organic", "vegetable peel": "Organic", "fruit peel": "Organic",
    "leftover food": "Organic", "tea bag": "Organic", "egg shell": "Organic",
    "garden waste": "Organic", "leaves": "Organic", "flowers": "Organic",
    "wood": "Organic", "coffee grounds": "Organic",

    # E-waste
    "battery": "E-waste", "mobile phone": "E-waste", "laptop": "E-waste",
    "charger": "E-waste", "cable": "E-waste", "circuit board": "E-waste",
    "led bulb": "E-waste", "television": "E-waste", "computer": "E-waste",
    "remote": "E-waste", "headphone": "E-waste", "power bank": "E-waste",

    # Hazardous
    "medicine": "Hazardous", "syringe": "Hazardous", "paint": "Hazardous",
    "chemical container": "Hazardous", "pesticide": "Hazardous", "thermometer": "Hazardous",
    "spray can": "Hazardous", "motor oil": "Hazardous", "sanitary waste": "Hazardous",
    "expired medicine": "Hazardous", "cleaning chemical": "Hazardous",
}

# Recommended disposal tip per category
DISPOSAL_TIPS = {
    "Recyclable": "Rinse if needed and place in the blue recycling bin.",
    "Organic": "Compost it or place in the green organic waste bin.",
    "E-waste": "Drop off at a certified e-waste collection center. Do not bin with regular waste.",
    "Hazardous": "Take to a hazardous waste facility. Never mix with household trash.",
    "General Waste": "Place in the general waste bin. Consider checking for reuse options first.",
}


def classify_waste(item_name: str) -> dict:
    """
    Classify a waste item by name.

    Args:
        item_name: name of the waste item entered/selected by the user.

    Returns:
        dict with keys: item, category, tip
    """
    if not item_name or not item_name.strip():
        return {"item": item_name, "category": "Unknown", "tip": "Please enter a valid item."}

    query = item_name.strip().lower()

    # Exact match
    if query in WASTE_DB:
        category = WASTE_DB[query]
    else:
        # Partial / substring match, then word-overlap match
        category = None
        for keyword, cat in WASTE_DB.items():
            if keyword in query or query in keyword:
                category = cat
                break
        if category is None:
            query_words = set(query.split())
            best_overlap = 0
            for keyword, cat in WASTE_DB.items():
                overlap = len(query_words & set(keyword.split()))
                if overlap > best_overlap:
                    best_overlap = overlap
                    category = cat
        if category is None:
            category = "General Waste"

    return {
        "item": item_name,
        "category": category,
        "tip": DISPOSAL_TIPS.get(category, "Dispose responsibly."),
    }


def get_all_items():
    """Return list of all known items, for use in a Streamlit dropdown."""
    return sorted(WASTE_DB.keys())


def get_categories():
    """Return list of unique categories."""
    return ["Recyclable", "Organic", "E-waste", "Hazardous", "General Waste"]


if __name__ == "__main__":
    # quick manual test
    for test_item in ["Plastic Bottle", "battery", "banana peel", "random unknown item"]:
        print(classify_waste(test_item))
