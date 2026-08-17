import os

from dotenv import load_dotenv
from openai import OpenAI

from hybrid_search import search_products
from prompt import build_prompt


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# 2. CREATE OPENAI CLIENT
# ============================================================

client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-5.4-mini"


# ============================================================
# TOKEN USAGE & COST TRACKING
# ============================================================

INPUT_COST_PER_MILLION = 0.75
OUTPUT_COST_PER_MILLION = 4.5

total_input_tokens = 0
total_output_tokens = 0
total_tokens = 0
total_cost = 0.0
llm_call_count = 0


def calculate_cost(input_tokens, output_tokens):
    """
    Calculate OpenAI API cost in USD.
    """

    input_cost = (
        input_tokens / 1_000_000
    ) * INPUT_COST_PER_MILLION

    output_cost = (
        output_tokens / 1_000_000
    ) * OUTPUT_COST_PER_MILLION

    total_cost = input_cost + output_cost

    return input_cost, output_cost, total_cost


def track_usage(response):
    """
    Extract token usage from the OpenAI response
    and update cumulative usage statistics.
    """

    global total_input_tokens
    global total_output_tokens
    global total_tokens
    global total_cost
    global llm_call_count

    usage = response.usage

    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    request_total_tokens = usage.total_tokens

    input_cost, output_cost, request_cost = calculate_cost(
        input_tokens,
        output_tokens
    )

    # Update cumulative totals
    total_input_tokens += input_tokens
    total_output_tokens += output_tokens
    total_tokens += request_total_tokens
    total_cost += request_cost
    llm_call_count += 1

    # Display usage for this request
    print("\n" + "-" * 60)
    print("LLM TOKEN USAGE")
    print("-" * 60)

    print(f"Input tokens:   {input_tokens:,}")
    print(f"Output tokens:  {output_tokens:,}")
    print(f"Total tokens:   {request_total_tokens:,}")

    print("\nLLM COST")
    print("-" * 60)

    print(f"Input cost:     ${input_cost:.6f}")
    print(f"Output cost:    ${output_cost:.6f}")
    print(f"Request cost:   ${request_cost:.6f}")

    print("-" * 60)

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": request_total_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": request_cost,
    }


def print_usage_summary():
    """
    Display cumulative token usage and cost.
    """

    print("\n")
    print("=" * 60)
    print("LLM USAGE & COST SUMMARY")
    print("=" * 60)

    print(f"LLM calls:       {llm_call_count:,}")
    print(f"Input tokens:    {total_input_tokens:,}")
    print(f"Output tokens:   {total_output_tokens:,}")
    print(f"Total tokens:    {total_tokens:,}")

    print("-" * 60)

    print(f"Total cost:      ${total_cost:.6f}")

    if llm_call_count > 0:
        average_cost = total_cost / llm_call_count
        print(f"Average/request: ${average_cost:.6f}")

    print("=" * 60)

# ============================================================
# 3. CONVERSATION STATE
# ============================================================

conversation_history = []

# Store the products returned by the most recent
# recommendation/search query.
last_retrieved_products = []

# Store the user's most recent query.
last_user_query = None

# Store the actual search query used for the most recent
# product search.
last_search_query = None

# Store filters/constraints from the previous search.
last_search_filters = {}


# ============================================================
# 4. BUILD RAG CONTEXT
# ============================================================

def build_context(products):
    """
    Convert retrieved products into text context
    for the LLM.
    """

    context_parts = []

    for i, product in enumerate(products, start=1):

        context = f"""
Product {i}
------------------------------
Product ID: {product.get("id")}
Category: {product.get("category")}
Brand: {product.get("brand")}
Model: {product.get("model")}
Colour: {product.get("colour")}
Price: ₹{product.get("price")}
Rating: {product.get("rating")}

Description:
{product.get("description")}
"""

        context_parts.append(context)

    return "\n".join(context_parts)


# ============================================================
# 5. DETECT FOLLOW-UP QUESTIONS
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

    # ========================================================
    # 1. REFERENCES TO PREVIOUS RESULTS
    # ========================================================

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

    # ========================================================
    # 2. BEST / RECOMMENDATION QUESTIONS
    # ========================================================

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

    # ========================================================
    # 3. COMPARISON QUESTIONS
    # ========================================================

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

    # ========================================================
    # 4. TOP / RANKING QUESTIONS
    # ========================================================

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

    # ========================================================
    # 5. PRODUCT FEATURE FOLLOW-UPS
    # ========================================================

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

    # ========================================================
    # 6. GENERAL FOLLOW-UP QUESTIONS
    # ========================================================

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

    # ========================================================
    # 7. CHECK ALL PATTERNS
    # ========================================================

    all_patterns = (
        reference_patterns
        + recommendation_patterns
        + comparison_patterns
        + ranking_patterns
        + feature_patterns
        + general_follow_up_patterns
    )

    for pattern in all_patterns:

        if pattern in query:
            return True

    return False

def is_new_constraint_query(user_query):
    """
    Detect whether the user wants a NEW product search
    while referring to constraints from the previous search.

    Examples:
        "show me something cheaper"
        "show me something under 40000"
        "find another one"
        "show me a cheaper option"
        "what about something below 50000"
    """

    query = user_query.lower().strip()

    new_search_patterns = [

        # ----------------------------------------------------
        # Cheaper requests
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Explicit price requests
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Another product / option
        # ----------------------------------------------------

        "another one",
        "another option",
        "another product",

        "show me another",
        "find another",
        "give me another",
    ]

    for pattern in new_search_patterns:

        if pattern in query:
            return True

    return False

def build_constraint_query(user_query):
    """
    Build a new search query by combining the previous
    search query with the user's new requirement.

    Example:

    Previous:
        Samsung gaming smartphone 30000 to 80000

    Current:
        show me something cheaper

    New query:
        Samsung gaming smartphone cheaper
    """

    if not last_search_query:
        return user_query

    query = user_query.lower().strip()

    previous_query = last_search_query

    # --------------------------------------------------------
    # Explicit price query
    # --------------------------------------------------------

    if any(
        phrase in query
        for phrase in [
            "under",
            "below",
            "less than",
            "within",
            "maximum",
            "max"
        ]
    ):

        return f"{previous_query} {user_query}"


    # --------------------------------------------------------
    # Cheaper request
    # --------------------------------------------------------

    if "cheaper" in query or "less expensive" in query:

        return f"{previous_query} cheaper"


    # --------------------------------------------------------
    # Another product / option
    # --------------------------------------------------------

    if any(
        phrase in query
        for phrase in [
            "another one",
            "another option",
            "another product",
            "show me another",
            "find another"
        ]
    ):

        return previous_query


    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return f"{previous_query} {user_query}"

def extract_price_constraint(user_query):
    """
    Extract a maximum price from simple queries such as:

        under 40000
        below 50000
        less than 60000
        within 70000

    Returns:
        float or None
    """

    import re

    query = user_query.lower()

    patterns = [
        r"(?:under|below|less than|maximum|max|within)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)",
        r"(?:₹|rs\.?|inr)\s*([0-9,]+)"
    ]

    for pattern in patterns:

        match = re.search(pattern, query)

        if match:

            price = match.group(1)

            price = price.replace(",", "")

            return float(price)

    return None

# ============================================================
# 6. RETRIEVE PRODUCTS
# ============================================================

def retrieve_products(user_query, top_k=5):
    """
    Retrieve products using the existing hybrid search.
    """

    products = search_products(
        query=user_query,
        top_k=top_k
    )

    return products


# ============================================================
# 7. GENERATE ANSWER
# ============================================================

def generate_answer(user_query, top_k=5):
    """
    Complete conversational RAG pipeline.

    Handles:

    1. New product searches
    2. Follow-up questions about previous products
    3. New searches that preserve previous constraints
    """

    global last_retrieved_products
    global last_user_query
    global last_search_query


    # ========================================================
    # STEP 1: DETECT QUERY TYPE
    # ========================================================

    follow_up = (
        bool(last_retrieved_products)
        and is_follow_up_question(user_query)
    )

    constraint_query = (
        bool(last_retrieved_products)
        and is_new_constraint_query(user_query)
    )


    # ========================================================
    # STEP 2: FOLLOW-UP ABOUT PREVIOUS PRODUCTS
    # ========================================================

    if follow_up:

        print("\nUsing previous retrieved products.")

        products = last_retrieved_products

        current_search_query = last_search_query


    # ========================================================
    # STEP 3: NEW SEARCH USING PREVIOUS CONSTRAINTS
    # ========================================================

    elif constraint_query:

        print(
            "\nPerforming new search "
            "with previous constraints."
        )

        current_search_query = build_constraint_query(
            user_query
        )

        print(
            "Expanded search query:",
            current_search_query
        )

        products = retrieve_products(
            user_query=current_search_query,
            top_k=top_k
        )


    # ========================================================
    # STEP 4: COMPLETELY NEW SEARCH
    # ========================================================

    else:

        print("\nPerforming new product search.")

        products = retrieve_products(
            user_query=user_query,
            top_k=top_k
        )

        current_search_query = user_query


    # ========================================================
    # STEP 5: HANDLE NO RESULTS
    # ========================================================

    if not products:

        answer = "I couldn't find any relevant products."

        conversation_history.append(
            f"User: {user_query}"
        )

        conversation_history.append(
            f"Assistant: {answer}"
        )

        return answer


    # ========================================================
    # STEP 6: BUILD RAG CONTEXT
    # ========================================================

    retrieved_chunks = build_context(
        products
    )


    # ========================================================
    # STEP 7: BUILD PROMPT
    # ========================================================

    prompt = build_prompt(
        user_query=user_query,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
        previous_user_query=last_user_query,
        is_follow_up=follow_up
    )


    # ========================================================
    # STEP 8: CALL OPENAI
    # ========================================================

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

        # Track token usage and cost
    track_usage(response)

    # ========================================================
    # STEP 9: GET ANSWER
    # ========================================================

    answer = response.output_text


    # ========================================================
    # STEP 10: SAVE CONVERSATION
    # ========================================================

    conversation_history.append(
        f"User: {user_query}"
    )

    conversation_history.append(
        f"Assistant: {answer}"
    )


    # ========================================================
    # STEP 11: UPDATE SEARCH STATE
    # ========================================================

    # For a NEW SEARCH or CONSTRAINT SEARCH,
    # replace the current recommendation set.

    if not follow_up:

        last_retrieved_products = products

        last_user_query = user_query

        last_search_query = current_search_query


    return answer


# ============================================================
# 8. DISPLAY RETRIEVED PRODUCTS
# ============================================================

def display_retrieved_products(products):

    print("\nRetrieved Products:")
    print("-" * 60)

    for i, product in enumerate(products, start=1):

        print(
            f"{i}. "
            f"{product.get('brand')} "
            f"{product.get('model')} "
            f"(Product ID: {product.get('id')})"
        )

        print(f"   Colour: {product.get('colour')}")
        print(f"   Price: ₹{product.get('price')}")
        print(f"   Rating: {product.get('rating')}")
        print()


# ============================================================
# 9. MAIN APPLICATION
# ============================================================

def main():

    print("=" * 60)
    print("AI SHOPPING ASSISTANT")
    print("=" * 60)

    print("\nAsk me anything about the available products.")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'clear' to start a new conversation.")

    while True:

        user_query = input("\nYou: ").strip()


        # ----------------------------------------------------
        # Ignore empty input
        # ----------------------------------------------------

        if not user_query:
            continue


        # ----------------------------------------------------
        # Exit
        # ----------------------------------------------------

        if user_query.lower() in {"exit", "quit"}:

            print_usage_summary()

            print("\nGoodbye!")
            break


        # ----------------------------------------------------
        # Clear conversation
        # ----------------------------------------------------

        if user_query.lower() == "clear":
            conversation_history.clear()

            global last_retrieved_products
            global last_user_query
            global last_search_query
            global last_search_filters

            last_retrieved_products = []
            last_user_query = None
            last_search_query = None
            last_search_filters = {}

            print("\nConversation history cleared.")

            continue


        # ----------------------------------------------------
        # Generate answer
        # ----------------------------------------------------

        try:

            answer = generate_answer(
                user_query=user_query,
                top_k=5
            )

            print("\nAssistant:")
            print(answer)

        except Exception as e:

            print(f"\nError: {e}")


# ============================================================
# 10. RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    main()