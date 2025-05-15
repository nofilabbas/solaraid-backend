import requests
import csv
import time

all_products = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Loop through pages 1 to 5
for page in range(1, 51):
    print(f"Fetching page {page}...")
    url = f"https://www.daraz.pk/catalog/?_keyori=ss&ajax=true&from=search_history&isFirstRequest=true&page={page}&q=solar%20panel"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        items = data.get("mods", {}).get("listItems", [])
        
        for item in items:
            title = item.get("name", "")
            if "solar panel" in title.lower():  # Filter condition
                all_products.append({
                    "title": title,
                    "price": item.get("priceShow"),
                    "rating": item.get("ratingScore"),
                    "reviews": item.get("review"),
                    "image": item.get("image"),
                    "product_link": "https:" + item.get("productUrl") if item.get("productUrl") else ""
                })
    else:
        print(f"Failed to fetch page {page} (status code {response.status_code})")
    
    time.sleep(1)  # To avoid overwhelming the server

# Save to CSV
csv_file = "daraz_solar_panels_filtered.csv"
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=all_products[0].keys())
    writer.writeheader()
    writer.writerows(all_products)

print(f"\n{len(all_products)} filtered products saved to {csv_file}")
