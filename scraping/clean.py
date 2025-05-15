import pandas as pd
import re

# Load the CSV file
df = pd.read_csv("daraz_solar_panels_filtered.csv")

# Function to extract brand from title
def extract_brand(title):
    match = re.match(r"([A-Z][a-zA-Z0-9]*)", title)
    return match.group(1) if match else "Unknown"

# Function to extract wattage from title
def extract_wattage(title):
    match = re.search(r"(\d+)\s*(watt|watts|w)\b", title.lower())
    return int(match.group(1)) if match else None

# Function to clean price and convert to float
def clean_price(price_str):
    try:
        price_str = re.sub(r"[^\d]", "", price_str)
        return float(price_str)
    except:
        return None

# Apply transformations
df_cleaned = pd.DataFrame()
df_cleaned['title'] = df['title']
df_cleaned['brand'] = df['title'].apply(extract_brand)
df_cleaned['wattage'] = df['title'].apply(extract_wattage)
df_cleaned['total_price'] = df['price'].apply(clean_price)

# Calculate price per watt
df_cleaned['price_per_watt'] = df_cleaned.apply(
    lambda row: round(row['total_price'] / row['wattage'], 2) if row['wattage'] and row['total_price'] else None,
    axis=1
)

# Filter for wattage between 500 and 700
df_filtered = df_cleaned[(df_cleaned['wattage'] >= 500) & (df_cleaned['wattage'] <= 700)]

# Save the cleaned and filtered data to CSV
df_filtered.to_csv("cleaned_solar_panels_filtered_500_700.csv", index=False)
