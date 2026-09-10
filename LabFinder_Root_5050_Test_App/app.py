from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

LAB_ITEMS = [
    {"name": "Benchtop Centrifuge", "category": "Centrifuge",
     "description": "Compact laboratory centrifuge for separating samples.",
     "price": 1299, "tags": ["centrifuge", "sample", "separation"]},
    {"name": "High-Speed Centrifuge", "category": "Centrifuge",
     "description": "High-speed centrifuge for advanced laboratory workflows.",
     "price": 4899, "tags": ["centrifuge", "high speed", "research"]},
    {"name": "Mini Microcentrifuge", "category": "Centrifuge",
     "description": "Small footprint microcentrifuge for routine lab work.",
     "price": 899, "tags": ["microcentrifuge", "centrifuge", "compact"]},
    {"name": "Digital Microscope", "category": "Microscope",
     "description": "Digital microscope with camera and image capture.",
     "price": 2199, "tags": ["microscope", "imaging", "camera"]},
    {"name": "Analytical Balance", "category": "Measurement",
     "description": "Precision balance for accurate laboratory measurements.",
     "price": 1599, "tags": ["balance", "measurement", "precision"]},
    {"name": "PCR Thermal Cycler", "category": "Molecular Biology",
     "description": "Programmable thermal cycler for PCR workflows.",
     "price": 3799, "tags": ["pcr", "thermal cycler", "molecular biology"]},
    {"name": "Laboratory Shaker", "category": "Shaker",
     "description": "Orbital shaker for controlled sample mixing.",
     "price": 1199, "tags": ["shaker", "mixing", "samples"]},
    {"name": "CO2 Incubator", "category": "Incubator",
     "description": "Temperature and CO2 controlled laboratory incubator.",
     "price": 5299, "tags": ["incubator", "co2", "cell culture"]},
]

TRENDING_ITEMS = [
    ("AI Smart Water Bottle", "TRENDING"),
    ("Viral LED Desk Lamp", "HOT"),
    ("Wireless Noise-Canceling Headphones", "POPULAR"),
    ("Smart Fitness Ring", "TRENDING"),
    ("3D Printing Pen", "HOT"),
    ("Robot Vacuum Pro", "POPULAR"),
]


def search_items(query="", category=""):
    results = LAB_ITEMS
    query = query.strip().lower()

    if query:
        results = [
            item for item in results
            if query in item["name"].lower()
            or query in item["category"].lower()
            or query in item["description"].lower()
            or any(query in tag.lower() for tag in item["tags"])
        ]

    if category:
        results = [
            item for item in results
            if item["category"].lower() == category.lower()
        ]

    return results


# ONLY APPLICATION URL:
# http://127.0.0.1:5050
@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    results = search_items(query, category)
    categories = sorted({item["category"] for item in LAB_ITEMS})

    return render_template(
        "index.html",
        query=query,
        category=category,
        results=results,
        categories=categories,
        trending=TRENDING_ITEMS,
    )


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "")
    return jsonify({"results": search_items(query)})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
