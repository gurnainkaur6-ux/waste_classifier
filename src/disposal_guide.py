"""
disposal_guide.py
-----------------
Maps each predicted category to bin colour, do's, don'ts and a tip.
Edit the text here to match your own city's local rules.
"""

DISPOSAL_GUIDE = {
    "Recyclable": {
        "icon": "♻️",
        "bin": "Blue Bin",
        "color": "#2563eb",
        "ink": "#ffffff",
        "summary": "Plastic and glass items that can be processed and reused.",
        "dos": [
            "Rinse bottles, jars and containers before disposal",
            "Remove caps and lids and sort them separately",
            "Flatten plastic bottles to save space",
        ],
        "donts": [
            "Don't put broken glass loose in the bin; wrap it safely",
            "Don't mix in food-soiled plastic",
            "Don't throw in plastic bags carrying other waste",
        ],
        "tip": "Look for the recycling number on plastic: 1 (PET) and 2 (HDPE) are the most widely accepted.",
    },
    "Organic": {
        "icon": "🌱",
        "bin": "Green Bin",
        "color": "#15803d",
        "ink": "#ffffff",
        "summary": "Food and vegetable waste that rots naturally and can become compost.",
        "dos": [
            "Collect kitchen scraps, peels and leftovers in the green bin",
            "Drain excess liquid before disposal",
            "Compost at home if you have a garden or balcony",
        ],
        "donts": [
            "Don't mix with plastic bags or packaging",
            "Don't add large amounts of oil or cooked meat to home compost",
            "Don't leave it uncollected for days; it attracts pests",
        ],
        "tip": "Composting organic waste cuts landfill load and gives you free fertiliser.",
    },
    "Paper": {
        "icon": "📄",
        "bin": "Blue Bin (Paper)",
        "color": "#0369a1",
        "ink": "#ffffff",
        "summary": "Paper and cardboard that can be pulped into new paper products.",
        "dos": [
            "Keep paper and cardboard dry and clean",
            "Flatten cardboard boxes",
            "Remove plastic tape and staples where possible",
        ],
        "donts": [
            "Don't recycle greasy pizza boxes or food-stained paper",
            "Don't include wet or soggy paper",
            "Don't mix tissue paper and used napkins with clean paper",
        ],
        "tip": "Paper can be recycled about 5 to 7 times, so keep it clean and dry.",
    },
    "Metal": {
        "icon": "🔩",
        "bin": "Yellow Bin",
        "color": "#facc15",
        "ink": "#1f2937",
        "summary": "Cans, tins and metal items that are highly recyclable.",
        "dos": [
            "Rinse food cans and tins",
            "Crush cans to save space",
            "Give large metal items to scrap dealers",
        ],
        "donts": [
            "Don't put aerosol cans with leftover contents in the bin",
            "Don't throw batteries along with metal waste",
            "Don't leave sharp edges exposed; fold or wrap them",
        ],
        "tip": "Recycling metal saves up to 90% of the energy needed to make it from raw ore (aluminium).",
    },
    "General Waste": {
        "icon": "🗑️",
        "bin": "Black Bin",
        "color": "#475569",
        "ink": "#ffffff",
        "summary": "Items that cannot be recycled or composted through normal household bins.",
        "dos": [
            "Hand over e-waste to an authorised e-waste collection centre",
            "Donate usable clothes and textiles",
            "Wrap sharp or hazardous items safely before disposal",
        ],
        "donts": [
            "Don't throw electronics, batteries or bulbs in the regular bin",
            "Don't burn waste in the open",
            "Don't mix with recyclables, which contaminates the batch",
        ],
        "tip": "Before binning, ask: can it be repaired, reused or donated?",
    },
}
