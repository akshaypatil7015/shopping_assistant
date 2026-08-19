import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from hybrid_search import search_products
from prompt import build_prompt
from rag import build_context

import conversation
import monitoring

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is not set. "
        "Please add it to your .env file."
    )


# ============================================================
# CREATE OPENAI CLIENT
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
# retrieve_products
# ============================================================
def retrieve_products(user_query, top_k=5):
    """
    Retrieve products using hybrid search
    and measure search latency.
    """

    start_time = time.perf_counter()

    products = search_products(
        query=user_query,
        top_k=top_k
    )

    search_latency = time.perf_counter() - start_time

    return products, search_latency


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(user_query, top_k=5):
    """
    Complete conversational RAG pipeline.

    Handles:

    1. New product searches
    2. Follow-up questions about previous products
    3. New searches that preserve previous constraints
    """
    request_start_time = time.perf_counter()

    # ========================================================
    # STEP 1: DETECT QUERY TYPE
    # ========================================================

    follow_up = (
    bool(conversation.last_retrieved_products)
    and conversation.is_follow_up_question(user_query)
    )

    constraint_query = (
        bool(conversation.last_retrieved_products)
        and conversation.is_new_constraint_query(user_query)
    )


    # ========================================================
    # STEP 2: FOLLOW-UP ABOUT PREVIOUS PRODUCTS
    # ========================================================

    if follow_up:

        print("\nUsing previous retrieved products.")

        products = conversation.last_retrieved_products

        current_search_query = conversation.last_search_query

        search_latency = 0.0


    # ========================================================
    # STEP 3: NEW SEARCH USING PREVIOUS CONSTRAINTS
    # ========================================================

    elif constraint_query:

        print(
            "\nPerforming new search "
            "with previous constraints."
        )

        current_search_query = conversation.build_constraint_query(
            user_query
        )

        print(
            "Expanded search query:",
            current_search_query
        )

        products, search_latency = retrieve_products(
            user_query=current_search_query,
            top_k=top_k
        )


    # ========================================================
    # STEP 4: COMPLETELY NEW SEARCH
    # ========================================================

    else:

        print("\nPerforming new product search.")

        products, search_latency = retrieve_products(
            user_query=user_query,
            top_k=top_k
        )

        current_search_query = user_query


    # ========================================================
    # STEP 5: HANDLE NO RESULTS
    # ========================================================

    if not products:

        answer = "I couldn't find any relevant products."

        conversation.conversation_history.append(
            f"User: {user_query}"
        )

        conversation.conversation_history.append(
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
    conversation_history=conversation.conversation_history,
    previous_user_query=conversation.last_user_query,
    is_follow_up=follow_up
)


    # ========================================================
    # STEP 8: CALL OPENAI
    # ========================================================

    llm_start_time = time.perf_counter()

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    llm_latency = time.perf_counter() - llm_start_time
    # Track token usage and cost
    usage_data = track_usage(response)

    # ========================================================
    # STEP 9: GET ANSWER
    # ========================================================

    answer = response.output_text
    total_latency = time.perf_counter() - request_start_time

    # ============================================================
    # DETERMINE QUERY TYPE
    # ============================================================

    if follow_up:
        query_type = "follow_up"

    elif constraint_query:
        query_type = "constraint_search"

    else:
        query_type = "new_search"


    monitoring.log_request(
        user_query=user_query,
        search_query=current_search_query,
        query_type=query_type,
        filters=None,
        retrieved_product_ids=[
            product.get("id")
            for product in products
        ],
        num_results=len(products),
        search_latency=search_latency,
        llm_latency=llm_latency,
        total_latency=total_latency,
        model=MODEL,
        input_tokens=usage_data["input_tokens"],
        output_tokens=usage_data["output_tokens"],
        total_tokens=usage_data["total_tokens"],
        llm_cost=usage_data["total_cost"],
        response=answer,
        error=None,
    )

    # ========================================================
    # STEP 10: SAVE CONVERSATION
    # ========================================================

    conversation.conversation_history.append(
        f"User: {user_query}"
    )

    conversation.conversation_history.append(
        f"Assistant: {answer}"
    )


    # ========================================================
    # STEP 11: UPDATE SEARCH STATE
    # ========================================================

    # For a NEW SEARCH or CONSTRAINT SEARCH,
    # replace the current recommendation set.

    if not follow_up:

        conversation.last_retrieved_products = products

        conversation.last_user_query = user_query

        conversation.last_search_query = current_search_query

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
            conversation.clear_conversation()

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

    monitoring.init_monitoring_db()

    main()