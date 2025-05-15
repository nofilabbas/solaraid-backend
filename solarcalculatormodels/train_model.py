import os
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "merged_solar_panels_with_city.csv")

# Load data
df = pd.read_csv(csv_path)

# Simulate synthetic load (you can adjust this if needed)
df["UserLoad"] = df["Wattage"] * 3.5  # simulated load in watt-hours

# Encode City
le_city = LabelEncoder()
df["CityEncoded"] = le_city.fit_transform(df["City"])

# Features and target
X = df[["Wattage", "CityEncoded", "UserLoad"]]
y = df["Price"]

# Train model
model = RandomForestRegressor()
model.fit(X, y)

# Save model and encoder to the same folder
joblib.dump(model, os.path.join(BASE_DIR, "model.pkl"))
joblib.dump(le_city, os.path.join(BASE_DIR, "city_encoder.pkl"))

print("Model trained and saved.")
