import pandas as pd
from sklearn.neighbors import NearestNeighbors
from . import models
from django.db.models import Avg, F

def recommend_products(customer_id, n_recommendations=3):
    # Fetch all interactions
    interactions = models.Interaction.objects.all().values('customer_id', 'product_id', 'interaction_type')
    df = pd.DataFrame(interactions)
    
    print("Received customer_id:", customer_id)
    print("Interaction customer_ids:", df['customer_id'].unique().tolist())

    customer_id = int(customer_id)
    
    # Check if the customer has any interactions
    if df.empty or customer_id not in df['customer_id'].values:
        # Top-rated products for new customers (no interactions)
        top_rated_products = models.Product.objects.annotate(
            average_rating=Avg('product_ratings__rating')
        ).filter(average_rating__gt=0).order_by(F('average_rating').desc())

        top_rated_products = top_rated_products[:n_recommendations]
        
        return [product.id for product in top_rated_products], "top_rated"

    # Create pivot table (Customer vs Products)
    pivot = df.pivot_table(index='customer_id', columns='product_id', aggfunc='size', fill_value=0)
    print(f"Pivot table created: {pivot}")
    
    # Ensure the pivot index is an integer type
    pivot_index = pivot.index.astype(int).tolist()

    # Check if the customer_id exists in the pivot index
    if customer_id not in pivot_index:
        print(f"Customer {customer_id} not found in pivot index.")
        return [], 'personalized'

    n_customers = pivot.shape[0]
    model = NearestNeighbors(metric='cosine', algorithm='brute')
    model.fit(pivot)

    n_neighbors = min(3, n_customers)
    distances, indices = model.kneighbors([pivot.loc[customer_id]], n_neighbors=n_neighbors)

    similar_customers = pivot.index[indices.flatten()].tolist()

    print(f"Similar customers: {similar_customers}")

    recommended_products = set()
    for similar_customer in similar_customers:
        products = df[df['customer_id'] == similar_customer]['product_id'].tolist()
        recommended_products.update(products)

    # Remove products already interacted by the user
    customer_products = set(df[df['customer_id'] == customer_id]['product_id'].tolist())
    final_recommendations = list(set(recommended_products) - set(customer_products))

    # If no recommendations are found, fall back to top-rated products
    if not final_recommendations:
        print("No personalized recommendations found. Falling back to top-rated products.")
        top_rated_products = models.Product.objects.annotate(
            average_rating=Avg('product_ratings__rating')
        ).filter(average_rating__gt=0).order_by(F('average_rating').desc())

        final_recommendations = [product.id for product in top_rated_products[:n_recommendations]]
        recommendation_source = 'top_rated'
    else:
        recommendation_source = 'personalized'

    print(f"Recommended products: {recommended_products}")
    print(f"Recommended products: {final_recommendations}")

    return final_recommendations[:n_recommendations], recommendation_source