import json
import sqlite3
import numpy as np

from embeddings import create_embedding
from database import DB_PATH, create_tables


DATA_PATH = "data/products_500.json"


def create_product_text(product):
    return f"""
    Category: {product['Category']}
    Brand: {product['brand']}
    Model: {product['model']}
    Colour: {product['colour']}
    Product Description: {product['product description']}
    Price: {product['price in INR']} INR
    Rating: {product['rating']}
    """.strip()


def build_index():

    create_tables()

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Remove existing products
    cursor.execute("DELETE FROM products")

    print(f"Creating embeddings for {len(products)} products...")

    for i, product in enumerate(products):

        text = create_product_text(product)

        embedding = create_embedding(text)

        embedding_blob = embedding.astype(np.float32).tobytes()

        cursor.execute("""
            INSERT INTO products (
                category,
                brand,
                model,
                colour,
                description,
                price,
                rating,
                embedding
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product["Category"],
            product["brand"],
            product["model"],
            product["colour"],
            product["product description"],
            product["price in INR"],
            product["rating"],
            embedding_blob
        ))

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(products)}")

    conn.commit()
    conn.close()

    print("Embedding index created successfully.")


if __name__ == "__main__":
    build_index()