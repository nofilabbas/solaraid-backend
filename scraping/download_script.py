import pandas as pd
import random

# Load your CSV
df = pd.read_csv(r"D:\Nofil\University\Solaraid FYP\Solaraidprj\merged_solar_panels_data.csv")

# List of city names to randomly assign
cities = ["Lahore", "Karachi", "Islamabad", "Faisalabad"]

# Add a new 'City' column with random choices
df['City'] = [random.choice(cities) for _ in range(len(df))]

# Save the updated CSV
df.to_csv("solar_panels_with_city.csv", index=False)

print("City column added successfully!")