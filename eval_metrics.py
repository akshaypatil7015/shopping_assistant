def precision_at_k(retrieved, relevant, k):

    retrieved = retrieved[:k]

    if len(retrieved) == 0:
        return 0.0

    relevant = set(relevant)

    hits = sum(
        1 for product_id in retrieved
        if product_id in relevant
    )

    return hits / len(retrieved)


def recall_at_k(retrieved, relevant, k):

    if len(relevant) == 0:
        return 0.0

    retrieved = retrieved[:k]

    relevant = set(relevant)

    hits = sum(
        1 for product_id in retrieved
        if product_id in relevant
    )

    return hits / len(relevant)


def reciprocal_rank(retrieved, relevant):

    relevant = set(relevant)

    for rank, product_id in enumerate(retrieved, start=1):

        if product_id in relevant:
            return 1 / rank

    return 0.0


def mean_reciprocal_rank(all_results):

    if not all_results:
        return 0.0

    scores = [
        reciprocal_rank(
            retrieved,
            relevant
        )
        for retrieved, relevant in all_results
    ]

    return sum(scores) / len(scores)