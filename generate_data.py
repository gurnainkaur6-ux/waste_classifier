"""
generate_data.py
----------------
Creates dataset/waste_data.csv with realistic, logically consistent waste records.

Now includes:
- More realistic noise and edge cases
- Ambiguous examples (wet paper, dirty recyclables)
- Label noise (~2% intentional mislabeling to simulate real-world annotation errors)
- More diverse combinations to avoid perfect memorization

Usage:
    python generate_data.py              # 1000 rows (default, better for ML)
    python generate_data.py --rows 2000
"""
import argparse
import os
import random

import pandas as pd

random.seed(42)

# material -> (category, allowed wet/dry, allowed textures, biodegradable value)
# The first item in each list is the most common value for that material.
MATERIALS = {
    "plastic":    ("Recyclable",    ["dry", "wet"], ["smooth", "flexible", "hard"],   "no"),
    "glass":      ("Recyclable",    ["dry"],        ["smooth", "hard"],               "no"),
    "paper":      ("Paper",         ["dry", "wet"], ["smooth", "soft", "rough"],      "yes"),
    "cardboard":  ("Paper",         ["dry", "wet"], ["rough", "hard", "flexible"],    "yes"),
    "metal":      ("Metal",         ["dry"],        ["hard", "smooth", "rough"],      "no"),
    "aluminum":   ("Metal",         ["dry"],        ["smooth", "hard"],               "no"),
    "food":       ("Organic",       ["wet", "dry"], ["soft", "smooth", "rough"],      "yes"),
    "vegetable":  ("Organic",       ["wet"],        ["soft", "rough", "smooth"],      "yes"),
    "textile":    ("General Waste", ["dry"],        ["soft", "flexible", "rough"],    "no"),
    "e-waste":    ("General Waste", ["dry"],        ["hard", "smooth"],               "no"),
    "rubber":     ("General Waste", ["dry"],        ["flexible", "rough"],            "no"),
    "foam":       ("General Waste", ["dry"],        ["soft", "flexible"],             "no"),
    "other":      ("General Waste", ["dry", "wet"], ["rough", "smooth", "flexible", "soft", "hard"], "no"),
}

# More balanced weights
WEIGHTS = {
    "plastic": 15, "glass": 10, "paper": 12, "cardboard": 10, "metal": 8, "aluminum": 7,
    "food": 12, "vegetable": 10, "textile": 6, "e-waste": 5, "rubber": 3, "foam": 2, "other": 5,
}


def pick(options, typical_prob=0.65):
    """Pick the first option with typical_prob, otherwise uniform random."""
    return options[0] if random.random() < typical_prob else random.choice(options)


def make_row(material):
    category, wet_dry, textures, bio = MATERIALS[material]
    
    # Add some realistic edge cases
    # Wet paper/cardboard -> sometimes contaminated, goes to General Waste
    if material in ("paper", "cardboard") and random.random() < 0.08:
        if random.choice([True, False]):  # wet and dirty
            category = "General Waste"
            wet_dry = ["wet"]
    
    # Biodegradable textiles (cotton, jute)
    if material == "textile" and random.random() < 0.15:
        bio = "yes"
    
    # Some "other" can be biodegradable (wood, bamboo)
    if material == "other" and random.random() < 0.20:
        bio = "yes"
    
    row = {
        "material_type": material,
        "wet_or_dry": pick(wet_dry, typical_prob=0.70),
        "texture": pick(textures, typical_prob=0.65),
        "biodegradable": bio,
        "category": category,
    }
    
    # Add ~2% label noise to simulate annotation errors
    if random.random() < 0.02:
        wrong_categories = ["Recyclable", "Paper", "Metal", "Organic", "General Waste"]
        wrong_categories.remove(category)
        row["category"] = random.choice(wrong_categories)
    
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1000, help="Number of samples to generate")
    args = parser.parse_args()

    materials = random.choices(list(WEIGHTS), weights=list(WEIGHTS.values()), k=args.rows)
    df = pd.DataFrame([make_row(m) for m in materials])

    os.makedirs("dataset", exist_ok=True)
    df.to_csv("dataset/waste_data.csv", index=False)

    print(f"✓ Saved dataset/waste_data.csv with {len(df)} rows")
    print(f"  Unique combinations: {df[['material_type', 'wet_or_dry', 'texture', 'biodegradable']].drop_duplicates().shape[0]}")
    print("\nCategory distribution:")
    print(df["category"].value_counts().to_string())
    print(f"\nMaterial types: {df['material_type'].nunique()}")
    print(df["material_type"].value_counts().to_string())


if __name__ == "__main__":
    main()
