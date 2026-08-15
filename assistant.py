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

MODEL = "gpt-5.6"


# ============================================================
# 3. BUILD RAG CONTEXT
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
# 4. RETRIEVE PRODUCTS
# ============================================================

def retrieve_products(user_query, top_k=5):
    """
    Retrieve relevant products using the existing
    hybrid search system.
    """

    products = search_products(
        query=user_query,
        top_k=top_k
    )

    return products


# ============================================================
# 5. GENERATE ANSWER
# ============================================================

def generate_answer(user_query, top_k=5):
    """
    Complete RAG pipeline:

    User Query
        ↓
    Hybrid Search
        ↓
    Retrieved Products
        ↓
    Build Context
        ↓
    Build Prompt
        ↓
    OpenAI LLM
        ↓
    Final Answer
    """

    # --------------------------------------------------------
    # Step 1: Retrieve products
    # --------------------------------------------------------

    products = retrieve_products(
        user_query=user_query,
        top_k=top_k
    )
    """
    # temporary debug print to see what products were retrieved remove it later
    print("\nDEBUG - Retrieved Products:")
    for product in products:
        print(product)
    """
    
    if not products:
        return "I couldn't find any relevant products."
    

    # --------------------------------------------------------
    # Step 2: Build context from retrieved products
    # --------------------------------------------------------

    retrieved_chunks = build_context(products)


    # --------------------------------------------------------
    # Step 3: Build prompt using prompt.py
    # --------------------------------------------------------

    prompt = build_prompt(
        user_query=user_query,
        retrieved_chunks=retrieved_chunks
    )


    # --------------------------------------------------------
    # Step 4: Send prompt to OpenAI
    # --------------------------------------------------------

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )


    # --------------------------------------------------------
    # Step 5: Return generated answer
    # --------------------------------------------------------

    return response.output_text


# ============================================================
# 6. MAIN APPLICATION
# ============================================================

def main():

    print("=" * 60)
    print("AI SHOPPING ASSISTANT")
    print("=" * 60)

    print("\nAsk me anything about the available products.")
    print("Type 'exit' or 'quit' to stop.")

    while True:

        user_query = input("\nYou: ").strip()

        # Ignore empty input
        if not user_query:
            continue

        # Exit application
        if user_query.lower() in {"exit", "quit"}:
            print("\nGoodbye!")
            break

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
# 7. RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    main()