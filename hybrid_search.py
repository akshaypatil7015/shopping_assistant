import sqlite3
import re
import numpy as np

from database import DB_PATH
from embeddings import create_embedding

from sentence_transformers import CrossEncoder


# Cross-encoder re-ranker
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

reranker = CrossEncoder(RERANKER_MODEL)

# ============================================================
# 1. COSINE SIMILARITY
# ============================================================

def cosine_similarity(a, b):

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


# ============================================================
# 2. TEXT TOKENIZATION
# ============================================================

def tokenize(text):

    return re.findall(r"\w+", text.lower())


# ============================================================
# 3. CREATE SEARCHABLE PRODUCT TEXT
# ============================================================

def create_search_text(product):

    return " ".join([
        str(product["category"]),
        str(product["brand"]),
        str(product["model"]),
        str(product["colour"]),
        str(product["description"])
    ]).lower()


# ============================================================
# 4. EXTRACT PRICE RANGE
# ============================================================

def extract_price_range(query):

    query_lower = query.lower()

    min_price = None
    max_price = None

    # --------------------------------------------------------
    # 30000 to 80000
    # 30000 - 80000
    # 30000–80000
    # --------------------------------------------------------

    range_pattern = re.search(
        r"(?:₹|rs\.?|inr)?\s*([\d,]+)"
        r"\s*(?:to|-|–|—)\s*"
        r"(?:₹|rs\.?|inr)?\s*([\d,]+)",
        query_lower
    )

    if range_pattern:

        min_price = float(
            range_pattern.group(1).replace(",", "")
        )

        max_price = float(
            range_pattern.group(2).replace(",", "")
        )

        return min_price, max_price

    # --------------------------------------------------------
    # under / below / less than / upto / up to
    # --------------------------------------------------------

    max_pattern = re.search(
        r"(?:under|below|less than|upto|up to)"
        r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+)",
        query_lower
    )

    if max_pattern:

        max_price = float(
            max_pattern.group(1).replace(",", "")
        )

        return min_price, max_price

    # --------------------------------------------------------
    # above / over / more than
    # --------------------------------------------------------

    min_pattern = re.search(
        r"(?:above|over|more than)"
        r"\s*(?:₹|rs\.?|inr)?\s*([\d,]+)",
        query_lower
    )

    if min_pattern:

        min_price = float(
            min_pattern.group(1).replace(",", "")
        )

        return min_price, max_price

    return min_price, max_price


# ============================================================
# 5. EXTRACT BRAND
# ============================================================

def extract_brand(query, products):

    query_lower = query.lower()

    # Get unique brands from database
    brands = set()

    for product in products:

        brand = str(product["brand"]).strip()

        if brand:
            brands.add(brand)

    # Longest first prevents partial matching problems
    sorted_brands = sorted(
        brands,
        key=len,
        reverse=True
    )

    for brand in sorted_brands:

        pattern = r"\b" + re.escape(
            brand.lower()
        ) + r"\b"

        if re.search(pattern, query_lower):

            return brand

    return None


# ============================================================
# 6. EXTRACT CATEGORY
# ============================================================

def extract_category(query, products):

    query_lower = query.lower()

    # Get unique categories from database
    categories = set()

    for product in products:

        category = str(
            product["category"]
        ).strip()

        if category:
            categories.add(category)

    # Longest first
    sorted_categories = sorted(
        categories,
        key=len,
        reverse=True
    )

    for category in sorted_categories:

        pattern = r"\b" + re.escape(
            category.lower()
        ) + r"\b"

        if re.search(pattern, query_lower):

            return category

    # --------------------------------------------------------
    # Common category aliases
    # --------------------------------------------------------

    category_aliases = {
        "phone": "Smartphones",
        "phones": "Smartphones",
        "smartphone": "Smartphones",
        "smartphones": "Smartphones",
    } # Add more aliases as needed

    for word, category in category_aliases.items():

        if re.search(
            r"\b" + re.escape(word) + r"\b",
            query_lower
        ):

            # Verify category exists in dataset
            for existing_category in categories:

                if existing_category.lower() == category.lower():

                    return existing_category

    return None


# ============================================================
# 7. EXTRACT QUERY INFORMATION
# ============================================================

def parse_query(query, products):

    min_price, max_price = extract_price_range(query)

    brand = extract_brand(
        query,
        products
    )

    category = extract_category(
        query,
        products
    )

    return {
        "brand": brand,
        "category": category,
        "min_price": min_price,
        "max_price": max_price
    }


# ============================================================
# 8. FILTER PRODUCTS
# ============================================================

def filter_products(
    products,
    brand=None,
    category=None,
    min_price=None,
    max_price=None
):

    filtered_products = []

    for product in products:

        # ----------------------------------------------------
        # Brand filter
        # ----------------------------------------------------

        if brand is not None:

            if str(product["brand"]).lower() != brand.lower():
                continue

        # ----------------------------------------------------
        # Category filter
        # ----------------------------------------------------

        if category is not None:

            if (
                str(product["category"]).lower()
                != category.lower()
            ):
                continue

        # ----------------------------------------------------
        # Price filter
        # ----------------------------------------------------

        price = float(product["price"])

        if min_price is not None:

            if price < min_price:
                continue

        if max_price is not None:

            if price > max_price:
                continue

        filtered_products.append(product)

    return filtered_products


# ============================================================
# 9. REMOVE FILTER TERMS FROM BM25 QUERY
# ============================================================

def clean_query_for_search(
    query,
    brand=None,
    category=None,
    min_price=None,
    max_price=None
):

    cleaned_query = query.lower()

    # --------------------------------------------------------
    # Remove price ranges
    # Example:
    # 40000 to 80000
    # 40000 - 80000
    # --------------------------------------------------------

    cleaned_query = re.sub(
        r"(?:₹|rs\.?|inr)?\s*[\d,]+"
        r"\s*(?:to|-|–|—)\s*"
        r"(?:₹|rs\.?|inr)?\s*[\d,]+",
        " ",
        cleaned_query
    )

    # --------------------------------------------------------
    # Remove individual price expressions
    # --------------------------------------------------------

    cleaned_query = re.sub(
        r"(?:under|below|less than|upto|up to|"
        r"above|over|more than)"
        r"\s*(?:₹|rs\.?|inr)?\s*[\d,]+",
        " ",
        cleaned_query
    )

    # --------------------------------------------------------
    # Remove remaining numbers
    # --------------------------------------------------------

    cleaned_query = re.sub(
        r"\b\d[\d,]*\b",
        " ",
        cleaned_query
    )

    # --------------------------------------------------------
    # Remove price-related words
    # --------------------------------------------------------

    price_words = [
        "under",
        "below",
        "less",
        "than",
        "upto",
        "up",
        "to",
        "above",
        "over",
        "more",
        "range",
        "between"
    ]

    for word in price_words:

        cleaned_query = re.sub(
            r"\b" + re.escape(word) + r"\b",
            " ",
            cleaned_query
        )

    # --------------------------------------------------------
    # Remove conversational/request words ONLY
    # --------------------------------------------------------

    request_words = [
        "suggest",
        "me",
        "find",
        "show",
        "give",
        "recommend",
        "recommendation",
        "please",
        "want",
        "looking",
        "for"
    ]

    for word in request_words:

        cleaned_query = re.sub(
            r"\b" + re.escape(word) + r"\b",
            " ",
            cleaned_query
        )

    # --------------------------------------------------------
    # Normalize spaces
    # --------------------------------------------------------

    cleaned_query = re.sub(
        r"\s+",
        " ",
        cleaned_query
    ).strip()

    return cleaned_query


# ============================================================
# 10. BM25
# ============================================================

def calculate_bm25(
    query_tokens,
    document_tokens,
    document_frequencies,
    avg_doc_length,
    total_documents,
    k1=1.5,
    b=0.75
):

    document_length = len(document_tokens)

    term_frequency = {}

    for token in document_tokens:

        term_frequency[token] = (
            term_frequency.get(token, 0) + 1
        )

    score = 0.0

    for term in query_tokens:

        if term not in term_frequency:
            continue

        tf = term_frequency[term]

        df = document_frequencies.get(term, 0)

        if df == 0:
            continue

        idf = np.log(
            1 + (
                (total_documents - df + 0.5)
                / (df + 0.5)
            )
        )

        numerator = tf * (k1 + 1)

        denominator = (
            tf
            + k1 * (
                1
                - b
                + b * (
                    document_length
                    / avg_doc_length
                )
            )
        )

        score += idf * (
            numerator / denominator
        )

    return score


# ============================================================
# 11. KEYWORD / BM25 SEARCH
# ============================================================

def keyword_search(
    query,
    products,
    top_k=20
):

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    documents = []

    for product in products:

        text = create_search_text(product)

        tokens = tokenize(text)

        documents.append(tokens)

    total_documents = len(documents)

    if total_documents == 0:
        return []

    document_frequencies = {}

    for tokens in documents:

        unique_tokens = set(tokens)

        for token in unique_tokens:

            document_frequencies[token] = (
                document_frequencies.get(token, 0) + 1
            )

    avg_doc_length = (
        sum(
            len(tokens)
            for tokens in documents
        )
        / total_documents
    )

    results = []

    for product, tokens in zip(
        products,
        documents
    ):

        score = calculate_bm25(
            query_tokens=query_tokens,
            document_tokens=tokens,
            document_frequencies=document_frequencies,
            avg_doc_length=avg_doc_length,
            total_documents=total_documents
        )

        results.append({
            "id": product["id"],
            "category": product["category"],
            "brand": product["brand"],
            "model": product["model"],
            "colour": product["colour"],
            "description": product["description"],
            "price": product["price"],
            "rating": product["rating"],
            "bm25_score": float(score)
        })

    results.sort(
        key=lambda x: x["bm25_score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# 12. VECTOR SEARCH
# ============================================================

def vector_search(
    query,
    products,
    top_k=20
):

    query_embedding = create_embedding(query)

    results = []

    for product in products:

        product_embedding = np.frombuffer(
            product["embedding"],
            dtype=np.float32
        )

        similarity = cosine_similarity(
            query_embedding,
            product_embedding
        )

        results.append({
            "id": product["id"],
            "category": product["category"],
            "brand": product["brand"],
            "model": product["model"],
            "colour": product["colour"],
            "description": product["description"],
            "price": product["price"],
            "rating": product["rating"],
            "similarity": float(similarity)
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# 13. RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    keyword_results,
    vector_results,
    top_k=5,
    k=60
):

    fused_results = {}

    # --------------------------------------------------------
    # BM25 results
    # --------------------------------------------------------

    for rank, result in enumerate(
        keyword_results,
        start=1
    ):

        product_id = result["id"]

        if product_id not in fused_results:

            fused_results[product_id] = {
                "id": product_id,
                "category": result["category"],
                "brand": result["brand"],
                "model": result["model"],
                "colour": result["colour"],
                "description": result["description"],
                "price": result["price"],
                "rating": result["rating"],
                "rrf_score": 0.0,
                "bm25_rank": None,
                "vector_rank": None,
                "bm25_score": 0.0,
                "similarity": 0.0
            }

        fused_results[product_id]["rrf_score"] += (
            1 / (k + rank)
        )

        fused_results[product_id]["bm25_rank"] = rank

        fused_results[product_id]["bm25_score"] = (
            result["bm25_score"]
        )

    # --------------------------------------------------------
    # Vector results
    # --------------------------------------------------------

    for rank, result in enumerate(
        vector_results,
        start=1
    ):

        product_id = result["id"]

        if product_id not in fused_results:

            fused_results[product_id] = {
                "id": product_id,
                "category": result["category"],
                "brand": result["brand"],
                "model": result["model"],
                "colour": result["colour"],
                "description": result["description"],
                "price": result["price"],
                "rating": result["rating"],
                "rrf_score": 0.0,
                "bm25_rank": None,
                "vector_rank": None,
                "bm25_score": 0.0,
                "similarity": 0.0
            }

        fused_results[product_id]["rrf_score"] += (
            1 / (k + rank)
        )

        fused_results[product_id]["vector_rank"] = rank

        fused_results[product_id]["similarity"] = (
            result["similarity"]
        )

    # --------------------------------------------------------
    # Final ranking
    # --------------------------------------------------------

    results = list(
        fused_results.values()
    )

    results.sort(
        key=lambda x: x["rrf_score"],
        reverse=True
    )

    return results[:top_k]


# ============================================================
# 14. LOAD PRODUCTS
# ============================================================

def load_products():

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

    rows = cursor.fetchall()

    conn.close()

    products = []

    for row in rows:

        (
            product_id,
            category,
            brand,
            model,
            colour,
            description,
            price,
            rating,
            embedding
        ) = row

        products.append({
            "id": product_id,
            "category": category,
            "brand": brand,
            "model": model,
            "colour": colour,
            "description": description,
            "price": price,
            "rating": rating,
            "embedding": embedding
        })

    return products



def rerank_products(query, products, top_k=5):
    """
    Re-rank products returned by hybrid search using a cross-encoder.

    Args:
        query: Original user query.
        products: Candidate products returned by RRF.
        top_k: Number of final products to return.

    Returns:
        Re-ranked top-k products.
    """

    if not products:
        return []

    # Create query-product pairs for the cross-encoder
    pairs = []

    for product in products:
        product_text = " ".join(
            str(product.get(field, ""))
            for field in [
                "brand",
                "model",
                "category",
                "colour",
                "product description",
            ]
        )

        pairs.append([query, product_text])

    # Calculate relevance scores
    scores = reranker.predict(pairs)

    # Attach scores to products
    scored_products = []

    for product, score in zip(products, scores):
        product_copy = product.copy()
        product_copy["rerank_score"] = float(score)
        scored_products.append(product_copy)

    # Highest relevance score first
    scored_products.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return scored_products[:top_k]


# ============================================================
# 15. HYBRID SEARCH
# ============================================================

def search_products(
    query,
    top_k=5
):

    # --------------------------------------------------------
    # Load products
    # --------------------------------------------------------

    products = load_products()

    if not products:
        return []

    # --------------------------------------------------------
    # Parse query
    # --------------------------------------------------------

    query_info = parse_query(
        query,
        products
    )

    brand = query_info["brand"]
    category = query_info["category"]
    min_price = query_info["min_price"]
    max_price = query_info["max_price"]

    # --------------------------------------------------------
    # Display detected filters
    # --------------------------------------------------------

    print("\nDetected filters:")

    print("Brand:", brand)
    print("Category:", category)
    print("Min Price:", min_price)
    print("Max Price:", max_price)

    # --------------------------------------------------------
    # Apply structured filters
    # --------------------------------------------------------

    filtered_products = filter_products(
        products=products,
        brand=brand,
        category=category,
        min_price=min_price,
        max_price=max_price
    )

    print(
        "Products after filtering:",
        len(filtered_products)
    )

    if not filtered_products:
        return []

    # --------------------------------------------------------
    # Clean query for BM25
    # --------------------------------------------------------

    search_query = clean_query_for_search(
        query=query,
        brand=brand,
        category=category,
        min_price=min_price,
        max_price=max_price
    )

    # --------------------------------------------------------
    # If cleaning removes everything, use original query
    # --------------------------------------------------------

    if not search_query:

        search_query = query

    print(
        "Search query:",
        search_query
    )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    keyword_results = keyword_search(
        query=search_query,
        products=filtered_products,
        top_k=20
    )

    # --------------------------------------------------------
    # Vector Search
    # --------------------------------------------------------

    vector_results = vector_search(
        query=query,
        products=filtered_products,
        top_k=20
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    hybrid_results = reciprocal_rank_fusion(
    keyword_results=keyword_results,
    vector_results=vector_results,
    top_k=20
)

# --------------------------------------------------------
# Cross-Encoder Re-ranking
# --------------------------------------------------------

    reranked_results = rerank_products(
        query=query,
        products=hybrid_results,
        top_k=top_k
    )

    return reranked_results