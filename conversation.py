import re


# ============================================================
# CONVERSATION STATE
# ============================================================

conversation_history = []

# Products returned by the most recent recommendation/search.
last_retrieved_products = []

# User's most recent query.
last_user_query = None

# Actual search query used for the most recent product search.
last_search_query = None

# Filters/constraints from the previous search.
last_search_filters = {}


# ============================================================
# FOLLOW-UP DETECTION
# ============================================================

def is_follow_up_question(user_query):
    """
    Detect whether the current query refers to
    products from the previous recommendation/search.

    Returns:
        True  -> use previous retrieved products
        False -> perform a new product search
    """

    query = user_query.lower().strip()

    reference_patterns = [
        "above",
        "from above",
        "the above",
        "above product",
        "above products",

        "previous",
        "previous product",
        "previous products",

        "these",
        "these products",
        "those",
        "those products",

        "that one",
        "that product",

        "first one",
        "second one",
        "third one",
        "fourth one",
        "fifth one",

        "first product",
        "second product",
        "third product",
        "fourth product",
        "fifth product",

        "first two",
        "first three",
    ]

    recommendation_patterns = [
        "which one is best",
        "which is best",
        "which one should i buy",
        "which should i buy",
        "what should i buy",
        "which one do you recommend",
        "which do you recommend",

        "which one is better",
        "which is better",

        "which one is cheaper",
        "which is cheaper",

        "which one is expensive",
        "which is expensive",
    ]

    comparison_patterns = [
        "compare",
        "comparison",
        "compare these",
        "compare those",
        "compare the",
        "compare first",
        "compare second",

        "rank them",
        "rank these",
        "rank those",
    ]

    ranking_patterns = [
        "top",
        "top 5",
        "top five",
        "top 3",
        "top three",

        "tell me top",
        "show me top",
        "give me top",

        "best ones",
        "best products",
        "best phones",
        "best smartphones",
    ]

    feature_patterns = [
        "which has the best camera",
        "which one has the best camera",
        "which has better camera",
        "which one has better camera",

        "which has the best battery",
        "which one has the best battery",
        "which has better battery",
        "which one has better battery",

        "which has the best performance",
        "which one has the best performance",
        "which has better performance",
        "which one has better performance",

        "which has the best display",
        "which one has the best display",
        "which has better display",
        "which one has better display",
    ]

    general_follow_up_patterns = [
        "tell me more",
        "show me more",
        "more about",
        "what about",
        "how about",
        "and the second",
        "and the first",
        "and the third",
    ]

    all_patterns = (
        reference_patterns
        + recommendation_patterns
        + comparison_patterns
        + ranking_patterns
        + feature_patterns
        + general_follow_up_patterns
    )

    return any(pattern in query for pattern in all_patterns)


# ============================================================
# NEW CONSTRAINT QUERY
# ============================================================

def is_new_constraint_query(user_query):
    """
    Detect whether the user wants a NEW product search
    while referring to constraints from the previous search.
    """

    query = user_query.lower().strip()

    new_search_patterns = [
        "something cheaper",
        "cheaper option",
        "cheaper one",
        "cheaper product",

        "find something cheaper",
        "find a cheaper",
        "show me a cheaper",
        "show me something cheaper",
        "give me a cheaper",

        "less expensive",
        "something less expensive",

        "something under",
        "something below",
        "something less than",

        "show me something under",
        "show me something below",
        "show me something less than",

        "find something under",
        "find something below",

        "what about under",
        "what about below",

        "another one",
        "another option",
        "another product",

        "show me another",
        "find another",
        "give me another",
    ]

    return any(
        pattern in query
        for pattern in new_search_patterns
    )


# ============================================================
# BUILD CONSTRAINT QUERY
# ============================================================

def build_constraint_query(user_query):
    """
    Combine the previous search query with the
    user's new requirement.
    """

    if not last_search_query:
        return user_query

    query = user_query.lower().strip()

    previous_query = last_search_query

    if any(
        phrase in query
        for phrase in [
            "under",
            "below",
            "less than",
            "within",
            "maximum",
            "max",
        ]
    ):
        return f"{previous_query} {user_query}"

    if "cheaper" in query or "less expensive" in query:
        return f"{previous_query} cheaper"

    if any(
        phrase in query
        for phrase in [
            "another one",
            "another option",
            "another product",
            "show me another",
            "find another",
        ]
    ):
        return previous_query

    return f"{previous_query} {user_query}"


# ============================================================
# PRICE CONSTRAINT
# ============================================================

def extract_price_constraint(user_query):
    """
    Extract a maximum price from simple queries.

    Examples:
        under 40000
        below 50000
        less than 60000
        within 70000

    Returns:
        float or None
    """

    query = user_query.lower()

    patterns = [
        r"(?:under|below|less than|maximum|max|within)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)",
        r"(?:₹|rs\.?|inr)\s*([0-9,]+)",
    ]

    for pattern in patterns:

        match = re.search(pattern, query)

        if match:
            price = match.group(1).replace(",", "")
            return float(price)

    return None


# ============================================================
# CLEAR CONVERSATION
# ============================================================

def clear_conversation():
    """
    Reset the complete conversation state.
    """

    global last_retrieved_products
    global last_user_query
    global last_search_query
    global last_search_filters

    conversation_history.clear()

    last_retrieved_products = []
    last_user_query = None
    last_search_query = None
    last_search_filters = {}