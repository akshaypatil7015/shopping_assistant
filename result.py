from hybrid_search import search_products


query = input("Enter your query: ")

results = search_products(
    query,
    top_k=5
)


for rank, result in enumerate(results, start=1):

    print("=" * 80)

    print("Rank:", rank)

    print("Brand:", result["brand"])
    print("Model:", result["model"])
    print("Colour:", result["colour"])
    print("Price:", result["price"])
    print("Rating:", result["rating"])

    print()

    print(
        "BM25 Score:",
        round(result["bm25_score"], 4)
    )

    print(
        "Vector Similarity:",
        round(result["similarity"], 4)
    )

    print(
        "RRF Score:",
        round(result["rrf_score"], 6)
    )

    print(
        "BM25 Rank:",
        result["bm25_rank"]
    )

    print(
        "Vector Rank:",
        result["vector_rank"]
    )

    print()

    print(
        "Description:",
        result["description"][:300]
    )

print("=" * 80)