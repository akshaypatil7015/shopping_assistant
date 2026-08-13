import sqlite3
import numpy as np

from database import DB_PATH
from embeddings import create_embedding


def cosine_similarity(a, b):

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


def search_products(query, top_k=5):

    query_embedding = create_embedding(query)

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            category,
            brand,
            model,
            colour,
            description,
            price,
            rating,
            embedding
        FROM products
    """)

    products = cursor.fetchall()

    conn.close()

    results = []

    for product in products:

        (
            product_id,
            category,
            brand,
            model,
            colour,
            description,
            price,
            rating,
            embedding_blob
        ) = product

        product_embedding = np.frombuffer(
            embedding_blob,
            dtype=np.float32
        )

        similarity = cosine_similarity(
            query_embedding,
            product_embedding
        )

        results.append({
            "id": product_id,
            "category": category,
            "brand": brand,
            "model": model,
            "colour": colour,
            "description": description,
            "price": price,
            "rating": rating,
            "similarity": float(similarity)
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:top_k]