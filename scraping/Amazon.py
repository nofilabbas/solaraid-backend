import requests
import json
import csv
import time

# API endpoint and headers
url = "https://real-time-amazon-data.p.rapidapi.com/search"
headers = {
    "x-rapidapi-key": "4cb12a8120msh9c1540959aeccbap15dd1cjsn512573e883aa",
    "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com"
}

filtered_products = []

# Loop through pages 1 to 5
for page in range(1, 6):
    print(f"Fetching page {page}...")
    querystring = {
        "query": "Battery",
        "page": str(page),
        "country": "US",
        "sort_by": "RELEVANCE",
        "product_condition": "ALL",
        "is_prime": "false",
        "deals_and_discounts": "NONE"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        products = data.get("data", {}).get("products", [])
        for product in products:
            title = product.get("product_title", "")
            if "battery" in title.lower():  # Filter condition
                filtered_products.append({
                    "title": title,
                    "price": product.get("product_price"),
                    "rating": product.get("product_star_rating"),
                    "number_of_reviews": product.get("product_num_ratings"),
                    "image_url": product.get("product_photo"),
                    "product_link": product.get("product_url")
                })
        print(f"Page {page} processed.")
        print(f"Found {len(products)} products on page {page}")

    else:
        print(f"Failed to fetch page {page}: {response.status_code}")

    time.sleep(1)  # Be kind to the API server

# Save to CSV
csv_file = "filtered_amazon_solar_panels.csv"
if filtered_products:
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=filtered_products[0].keys())
        writer.writeheader()
        writer.writerows(filtered_products)
    print(f"\n{len(filtered_products)} filtered products saved to {csv_file}")
else:
    print("No matching products found.")
