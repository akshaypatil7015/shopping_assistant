import json

from eval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

from hybrid_search import (
    load_products,
    keyword_search,
    vector_search,
    reciprocal_rank_fusion,
    clean_query_for_search,
    parse_query,
    filter_products,
)


# ============================================================
# CONFIGURATION
# ============================================================

EVALUATION_FILE = "evaluation_queries.json"

K = 10

# BM25 and Vector search retrieve more candidates
# before RRF combines them.
RETRIEVAL_K = 20


# ============================================================
# LOAD EVALUATION QUERIES
# ============================================================

def load_evaluation_queries():

    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# GET RELEVANT PRODUCT IDS
# ============================================================

def get_relevant_product_ids(item):
    """
    Support both formats currently present
    in evaluation_queries.json:

        "product_ids": [1, 2, 3]

    and

        "relevant_products": [1, 2, 3]
    """

    if "product_ids" in item:

        return set(
            item["product_ids"]
        )

    if "relevant_products" in item:

        return set(
            item["relevant_products"]
        )

    return set()


# ============================================================
# PREPARE PRODUCTS
# ============================================================

def prepare_products(query, products):
    """
    Apply the same structured filtering logic used
    by the production hybrid search.

    This keeps the evaluation consistent with the
    actual shopping assistant retrieval pipeline.
    """

    query_info = parse_query(
        query,
        products
    )

    brand = query_info["brand"]
    category = query_info["category"]
    min_price = query_info["min_price"]
    max_price = query_info["max_price"]

    filtered_products = filter_products(
        products=products,
        brand=brand,
        category=category,
        min_price=min_price,
        max_price=max_price
    )

    return filtered_products, brand, category, min_price, max_price


# ============================================================
# BM25 SEARCH FOR EVALUATION
# ============================================================

def bm25_search_for_evaluation(
    query,
    products
):

    (
        filtered_products,
        brand,
        category,
        min_price,
        max_price
    ) = prepare_products(
        query,
        products
    )

    if not filtered_products:

        return []

    search_query = clean_query_for_search(
        query=query,
        brand=brand,
        category=category,
        min_price=min_price,
        max_price=max_price
    )

    if not search_query:

        search_query = query

    return keyword_search(
        query=search_query,
        products=filtered_products,
        top_k=RETRIEVAL_K
    )


# ============================================================
# VECTOR SEARCH FOR EVALUATION
# ============================================================

def vector_search_for_evaluation(
    query,
    products
):

    (
        filtered_products,
        _,
        _,
        _,
        _
    ) = prepare_products(
        query,
        products
    )

    if not filtered_products:

        return []

    return vector_search(
        query=query,
        products=filtered_products,
        top_k=RETRIEVAL_K
    )


# ============================================================
# HYBRID SEARCH FOR EVALUATION
# ============================================================

def hybrid_search_for_evaluation(
    query,
    products
):

    (
        filtered_products,
        brand,
        category,
        min_price,
        max_price
    ) = prepare_products(
        query,
        products
    )

    if not filtered_products:

        return []

    search_query = clean_query_for_search(
        query=query,
        brand=brand,
        category=category,
        min_price=min_price,
        max_price=max_price
    )

    if not search_query:

        search_query = query

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    keyword_results = keyword_search(
        query=search_query,
        products=filtered_products,
        top_k=RETRIEVAL_K
    )

    # --------------------------------------------------------
    # Vector Search
    # --------------------------------------------------------

    vector_results = vector_search(
        query=query,
        products=filtered_products,
        top_k=RETRIEVAL_K
    )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    hybrid_results = reciprocal_rank_fusion(
        keyword_results=keyword_results,
        vector_results=vector_results,
        top_k=K
    )

    return hybrid_results


# ============================================================
# EVALUATE ONE SEARCH METHOD
# ============================================================

def evaluate_search_method(
    search_function,
    evaluation_queries,
    products
):

    precision_scores = []
    recall_scores = []
    mrr_scores = []

    evaluated_queries = 0

    for item in evaluation_queries:

        query = item["query"]

        relevant_products = get_relevant_product_ids(
            item
        )

        # ----------------------------------------------------
        # Skip queries without known relevant products
        # ----------------------------------------------------

        if not relevant_products:

            continue

        results = search_function(
            query,
            products
        )

        retrieved_ids = [
            result["id"]
            for result in results[:K]
        ]

        # ----------------------------------------------------
        # Precision
        # ----------------------------------------------------

        precision = precision_at_k(
            retrieved_ids,
            relevant_products,
            K
        )

        # ----------------------------------------------------
        # Recall
        # ----------------------------------------------------

        recall = recall_at_k(
            retrieved_ids,
            relevant_products,
            K
        )

        # ----------------------------------------------------
        # MRR
        # ----------------------------------------------------

        mrr = reciprocal_rank(
            retrieved_ids,
            relevant_products
        )

        precision_scores.append(
            precision
        )

        recall_scores.append(
            recall
        )

        mrr_scores.append(
            mrr
        )

        evaluated_queries += 1

    if evaluated_queries == 0:

        return {
            "precision@10": 0.0,
            "recall@10": 0.0,
            "MRR": 0.0,
            "queries": 0
        }

    return {

        "precision@10":
            sum(precision_scores)
            / evaluated_queries,

        "recall@10":
            sum(recall_scores)
            / evaluated_queries,

        "MRR":
            sum(mrr_scores)
            / evaluated_queries,

        "queries":
            evaluated_queries
    }


# ============================================================
# PRINT RESULTS
# ============================================================

def print_results(
    method_name,
    results
):

    print(
        f"\n{method_name}"
    )

    print("-" * 50)

    print(
        f"Precision@10 : "
        f"{results['precision@10']:.4f}"
    )

    print(
        f"Recall@10    : "
        f"{results['recall@10']:.4f}"
    )

    print(
        f"MRR          : "
        f"{results['MRR']:.4f}"
    )

    print(
        f"Queries      : "
        f"{results['queries']}"
    )


# ============================================================
# MAIN EVALUATION
# ============================================================

def main():

    print("=" * 60)
    print("RETRIEVAL EVALUATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load evaluation queries
    # --------------------------------------------------------

    evaluation_queries = (
        load_evaluation_queries()
    )

    print(
        f"\nTotal evaluation entries: "
        f"{len(evaluation_queries)}"
    )

    # --------------------------------------------------------
    # Count valid queries
    # --------------------------------------------------------

    valid_queries = sum(
        1
        for item in evaluation_queries
        if get_relevant_product_ids(item)
    )

    skipped_queries = (
        len(evaluation_queries)
        - valid_queries
    )

    print(
        f"Queries with relevant products: "
        f"{valid_queries}"
    )

    print(
        f"Queries skipped: "
        f"{skipped_queries}"
    )

    # --------------------------------------------------------
    # Load products
    # --------------------------------------------------------

    products = load_products()

    print(
        f"Products in knowledge base: "
        f"{len(products)}"
    )

    # ========================================================
    # BM25
    # ========================================================

    print("\nEvaluating BM25...")

    bm25_results = evaluate_search_method(
        search_function=bm25_search_for_evaluation,
        evaluation_queries=evaluation_queries,
        products=products
    )

    # ========================================================
    # VECTOR
    # ========================================================

    print("\nEvaluating Vector Search...")

    vector_results = evaluate_search_method(
        search_function=vector_search_for_evaluation,
        evaluation_queries=evaluation_queries,
        products=products
    )

    # ========================================================
    # HYBRID
    # ========================================================

    print("\nEvaluating Hybrid + RRF...")

    hybrid_results = evaluate_search_method(
        search_function=hybrid_search_for_evaluation,
        evaluation_queries=evaluation_queries,
        products=products
    )

    # ========================================================
    # RESULTS
    # ========================================================

    print("\n")
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    print_results(
        "BM25",
        bm25_results
    )

    print_results(
        "Vector Search",
        vector_results
    )

    print_results(
        "Hybrid + RRF",
        hybrid_results
    )

    # ========================================================
    # FIND BEST METHOD
    # ========================================================

    methods = {
        "BM25": bm25_results,
        "Vector Search": vector_results,
        "Hybrid + RRF": hybrid_results
    }

    # Use MRR as the primary ranking metric.
    best_method = max(
        methods,
        key=lambda name: methods[name]["MRR"]
    )

    print("\n")
    print("=" * 60)
    print("BEST RETRIEVAL METHOD")
    print("=" * 60)

    print(
        f"\n{best_method}"
    )

    print(
        f"MRR: "
        f"{methods[best_method]['MRR']:.4f}"
    )

    print(
        f"Precision@10: "
        f"{methods[best_method]['precision@10']:.4f}"
    )

    print(
        f"Recall@10: "
        f"{methods[best_method]['recall@10']:.4f}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()