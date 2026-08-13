from search import search_products


query =input("Enter your query: ")

results = search_products(
    query,
    top_k=5
)


for result in results:

    print("=" * 80)

    print("Brand:", result["brand"])
    print("Model:", result["model"])
    print("Price:", result["price"])
    print("Rating:", result["rating"])

    print(
        "Similarity:",
        round(result["similarity"], 4)
    )

    print(
        "Description:",
        result["description"][:300]
    )