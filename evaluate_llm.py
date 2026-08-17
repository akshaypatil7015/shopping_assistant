import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from hybrid_search import search_products
from prompt import build_prompt as build_prompt_a


# ============================================================
# 1. LOAD ENVIRONMENT
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is not set. "
        "Please add it to your .env file."
    )


client = OpenAI(api_key=OPENAI_API_KEY)

MODEL = "gpt-5.6"


# ============================================================
# 2. FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

EVALUATION_FILE = (
    BASE_DIR / "data" / "llm_evaluation_queries.json"
)

RESULT_FILE = (
    BASE_DIR / "data" / "llm_evaluation_results.json"
)


# ============================================================
# 3. LOAD EVALUATION QUERIES
# ============================================================

def load_evaluation_queries():

    with open(
        EVALUATION_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# 4. BUILD PRODUCT CONTEXT
# ============================================================

def build_context(products):

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
# 5. IMPROVED PROMPT - APPROACH B
# ============================================================

def build_prompt_b(
    user_query,
    retrieved_chunks,
    conversation_history=None,
    previous_user_query=None,
    is_follow_up=False
):
    """
    Improved structured RAG prompt.

    This is Approach B.

    Approach A = existing prompt.py
    Approach B = this prompt
    """

    if conversation_history:

        history_text = "\n".join(
            conversation_history
        )

    else:

        history_text = "No previous conversation."

    previous_query_text = (
        previous_user_query
        if previous_user_query
        else "None"
    )

    prompt = f"""
You are an AI shopping assistant for a smartphone
e-commerce catalog.

Your task is to answer the user's question using
ONLY the information available in the retrieved
product context and the conversation history.

==================================================
CONVERSATION HISTORY
==================================================

{history_text}

==================================================
PREVIOUS USER QUERY
==================================================

{previous_query_text}

==================================================
CURRENT USER QUESTION
==================================================

{user_query}

==================================================
RETRIEVED PRODUCT CONTEXT
==================================================

{retrieved_chunks}

==================================================
ANSWERING RULES
==================================================

1. Use the retrieved product context as the primary
   factual source.

2. Do NOT invent product information.

3. Do NOT invent:
   - processor specifications
   - RAM
   - storage
   - battery capacity
   - charging technology
   - camera specifications
   - display specifications
   - ratings
   - prices
   - colours
   - features

4. If a requested specification is not present in the
   retrieved context, explicitly say that the available
   product information does not specify it.

5. Never use outside knowledge to fill missing
   product information.

6. Preserve constraints from the previous conversation
   when the user asks a follow-up question.

7. Important constraints include:
   - brand
   - budget
   - minimum price
   - maximum price
   - product type
   - gaming
   - camera
   - battery
   - display
   - other explicitly stated requirements

8. If the user asks:
   "which one is best?"
   "which one should I buy?"
   "which is better?"
   use the products currently being discussed.

9. Do NOT introduce products that are not in the
   retrieved context when answering a follow-up.

10. If the user asks for a comparison, compare only
    the products available in the retrieved context.

11. If the user asks about a specific product,
    identify it using brand, model, and Product ID
    whenever available.

12. If multiple products are recommended, explain
    briefly why each one matches the request.

13. Do not claim stock availability or purchase
    availability unless explicitly provided.

14. For "best" recommendations, consider the user's
    stated requirements first.

15. Do not automatically assume that the highest
    rating is always the best product.

16. If the requested product category is not available
    in the catalog, clearly explain that the catalog
    currently contains smartphones.

17. If the question cannot be answered reliably from
    the retrieved context, say so instead of guessing.

18. Keep the answer concise and useful.

19. Use bullet points or tables when they make the
    comparison easier to understand.

20. Answer the current question directly.

==================================================
SPECIAL FOLLOW-UP RULE
==================================================

Current query is considered a follow-up:

{is_follow_up}

If it is a follow-up, use the conversation history
and previous user query to resolve references such as:

- first product
- second product
- above
- previous
- these
- those
- that one
- which one
- cheaper one

Do not reinterpret these references as a completely
new product search.

==================================================

FINAL ANSWER
"""

    return prompt


# ============================================================
# 6. GET RETRIEVED PRODUCTS
# ============================================================

def retrieve_products(query, top_k=5):

    products = search_products(
        query=query,
        top_k=top_k
    )

    return products


# ============================================================
# 7. GENERATE ANSWER
# ============================================================

def generate_answer(prompt):

    response = client.responses.create(
        model=MODEL,
        input=prompt
    )

    return response.output_text.strip()


# ============================================================
# 8. PREPARE EVALUATION CONTEXT
# ============================================================

def prepare_evaluation_case(item):

    query = item["query"]
    query_type = item["type"]

    conversation_history = []
    previous_user_query = None

    is_follow_up = query_type in {
        "follow_up",
        "constraint_follow_up"
    }

    # --------------------------------------------------------
    # Follow-up queries need previous conversation context.
    # --------------------------------------------------------

    if query_type == "follow_up":

        seed_query = (
            "Suggest me a Samsung smartphone under 80000"
        )

        products = retrieve_products(
            seed_query,
            top_k=5
        )

        previous_user_query = seed_query

        conversation_history = [
            f"User: {seed_query}"
        ]

    # --------------------------------------------------------
    # Constraint follow-ups need the previous search context.
    # --------------------------------------------------------

    elif query_type == "constraint_follow_up":

        seed_query = (
            "Suggest me a Samsung gaming smartphone "
            "between 30000 and 80000"
        )

        # Combine the previous requirement with the
        # new requirement so that both prompts receive
        # the same relevant retrieved context.
        retrieval_query = (
            f"{seed_query}. {query}"
        )

        products = retrieve_products(
            retrieval_query,
            top_k=5
        )

        previous_user_query = seed_query

        conversation_history = [
            f"User: {seed_query}"
        ]

    # --------------------------------------------------------
    # Normal queries
    # --------------------------------------------------------

    else:

        products = retrieve_products(
            query,
            top_k=5
        )

    return (
        products,
        conversation_history,
        previous_user_query,
        is_follow_up
    )


# ============================================================
# 9. EVALUATE ONE QUERY
# ============================================================

def evaluate_query(item):

    query = item["query"]
    query_type = item["type"]

    print()
    print("=" * 70)
    print(f"Query {item['id']}: {query}")
    print(f"Type: {query_type}")
    print("=" * 70)

    # --------------------------------------------------------
    # Retrieve ONCE.
    #
    # Both prompts receive exactly the same products.
    # --------------------------------------------------------

    (
        products,
        conversation_history,
        previous_user_query,
        is_follow_up
    ) = prepare_evaluation_case(item)

    if not products:

        print("No products retrieved.")

        return {
            "id": item["id"],
            "query": query,
            "type": query_type,
            "retrieved_products": [],
            "prompt_a_answer": None,
            "prompt_b_answer": None,
            "judge": None,
            "error": "No products retrieved"
        }

    retrieved_chunks = build_context(products)

    retrieved_product_ids = [
        product.get("id")
        for product in products
    ]

    # ========================================================
    # APPROACH A
    # ========================================================

    prompt_a = build_prompt_a(
        user_query=query,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
        previous_user_query=previous_user_query,
        is_follow_up=is_follow_up
    )

    print("\nGenerating Prompt A answer...")

    answer_a = generate_answer(prompt_a)

    # ========================================================
    # APPROACH B
    # ========================================================

    prompt_b = build_prompt_b(
        user_query=query,
        retrieved_chunks=retrieved_chunks,
        conversation_history=conversation_history,
        previous_user_query=previous_user_query,
        is_follow_up=is_follow_up
    )

    print("Generating Prompt B answer...")

    answer_b = generate_answer(prompt_b)

    # ========================================================
    # JUDGE
    # ========================================================

    judge_result = judge_answers(
        query=query,
        retrieved_chunks=retrieved_chunks,
        answer_a=answer_a,
        answer_b=answer_b
    )

    print("\nPrompt A:")
    print(answer_a)

    print("\nPrompt B:")
    print(answer_b)

    print("\nJudge:")
    print(json.dumps(
        judge_result,
        indent=2
    ))

    return {
        "id": item["id"],
        "query": query,
        "type": query_type,
        "retrieved_product_ids": retrieved_product_ids,
        "prompt_a_answer": answer_a,
        "prompt_b_answer": answer_b,
        "judge": judge_result
    }


# ============================================================
# 10. LLM JUDGE
# ============================================================

def judge_answers(
    query,
    retrieved_chunks,
    answer_a,
    answer_b
):
    """
    Compare Prompt A and Prompt B.

    Scores:

    Relevance              1-5
    Groundedness           1-5
    Constraint adherence   1-5
    Answer quality         1-5

    The judge also selects the better answer.
    """

    judge_prompt = f"""
You are evaluating two answers produced by an
AI smartphone shopping assistant.

Evaluate them using ONLY the user question and
retrieved product context below.

==================================================
USER QUESTION
==================================================

{query}

==================================================
RETRIEVED PRODUCT CONTEXT
==================================================

{retrieved_chunks}

==================================================
ANSWER A
==================================================

{answer_a}

==================================================
ANSWER B
==================================================

{answer_b}

==================================================
EVALUATION CRITERIA
==================================================

Score each answer from 1 to 5.

1. RELEVANCE

Does the answer directly answer the user's question?

1 = does not answer the question
5 = directly and completely answers the question

2. GROUNDEDNESS

Are product-related factual claims supported by
the retrieved product context?

1 = many unsupported/invented claims
5 = factual claims are fully supported

3. CONSTRAINT ADHERENCE

Does the answer respect the user's requirements,
such as brand, budget, category, and features?

1 = ignores important constraints
5 = correctly follows the constraints

4. ANSWER QUALITY

Is the answer clear, concise, useful, and well structured?

1 = poor answer
5 = excellent answer

==================================================
IMPORTANT
==================================================

Do NOT reward an answer for using outside knowledge.

If information is missing from the retrieved context,
a good answer should acknowledge that rather than
inventing the information.

==================================================
OUTPUT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
  "answer_a": {{
    "relevance": 1,
    "groundedness": 1,
    "constraint_adherence": 1,
    "answer_quality": 1,
    "total": 4
  }},
  "answer_b": {{
    "relevance": 1,
    "groundedness": 1,
    "constraint_adherence": 1,
    "answer_quality": 1,
    "total": 4
  }},
  "winner": "A",
  "reason": "Brief explanation"
}}

The total must be the sum of the four scores.
"""

    response = client.responses.create(
        model=MODEL,
        input=judge_prompt
    )

    text = response.output_text.strip()

    # --------------------------------------------------------
    # Remove markdown code fences if the model adds them.
    # --------------------------------------------------------

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    try:

        return json.loads(text)

    except json.JSONDecodeError:

        return {
            "error": "Judge returned invalid JSON",
            "raw_response": text
        }


# ============================================================
# 11. CALCULATE SUMMARY
# ============================================================

def calculate_summary(results):

    valid_results = [
        result
        for result in results
        if result.get("judge")
        and "error" not in result["judge"]
    ]

    if not valid_results:

        return {}

    metrics = [
        "relevance",
        "groundedness",
        "constraint_adherence",
        "answer_quality",
        "total"
    ]

    summary = {
        "queries_evaluated": len(valid_results),
        "prompt_a": {},
        "prompt_b": {},
        "wins": {
            "A": 0,
            "B": 0,
            "Tie": 0
        }
    }

    # --------------------------------------------------------
    # Average scores
    # --------------------------------------------------------

    for prompt_name in ["a", "b"]:

        for metric in metrics:

            values = []

            for result in valid_results:

                scores = result["judge"][
                    f"answer_{prompt_name}"
                ]

                values.append(
                    scores[metric]
                )

            summary[
                f"prompt_{prompt_name}"
            ][metric] = round(
                sum(values) / len(values),
                4
            )

    # --------------------------------------------------------
    # Wins
    # --------------------------------------------------------

    for result in valid_results:

        winner = result["judge"].get(
            "winner"
        )

        if winner == "A":
            summary["wins"]["A"] += 1

        elif winner == "B":
            summary["wins"]["B"] += 1

        else:
            summary["wins"]["Tie"] += 1

    # --------------------------------------------------------
    # Overall winner
    # --------------------------------------------------------

    score_a = summary["prompt_a"]["total"]
    score_b = summary["prompt_b"]["total"]

    if score_a > score_b:

        summary["best_prompt"] = "Prompt A"

    elif score_b > score_a:

        summary["best_prompt"] = "Prompt B"

    else:

        summary["best_prompt"] = "Tie"

    return summary


# ============================================================
# 12. MAIN EVALUATION
# ============================================================

def main():

    print("=" * 70)
    print("LLM GENERATION EVALUATION")
    print("=" * 70)

    queries = load_evaluation_queries()

    print(
        f"\nTotal evaluation queries: {len(queries)}"
    )

    results = []

    # --------------------------------------------------------
    # Optional evaluation limit
    #
    # Example:
    #
    # EVAL_LIMIT=5 uv run evaluate_llm.py
    #
    # This is useful for testing before running all 40.
    # --------------------------------------------------------

    eval_limit = os.getenv(
        "EVAL_LIMIT"
    )

    if eval_limit:

        try:

            limit = int(eval_limit)

            queries = queries[:limit]

            print(
                f"Evaluation limit enabled: {limit}"
            )

        except ValueError:

            print(
                "Invalid EVAL_LIMIT. "
                "Running all queries."
            )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    for item in queries:

        try:

            result = evaluate_query(
                item
            )

            results.append(
                result
            )

        except Exception as e:

            print(
                f"\nERROR evaluating query "
                f"{item['id']}: {e}"
            )

            results.append({
                "id": item["id"],
                "query": item["query"],
                "type": item["type"],
                "error": str(e)
            })

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = calculate_summary(
        results
    )

    print("\n")
    print("=" * 70)
    print("LLM EVALUATION RESULTS")
    print("=" * 70)

    print(
        f"\nQueries evaluated: "
        f"{summary.get('queries_evaluated', 0)}"
    )

    if summary:

        print("\nPrompt A")
        print("-" * 40)

        print(
            "Relevance:",
            summary["prompt_a"]["relevance"]
        )

        print(
            "Groundedness:",
            summary["prompt_a"]["groundedness"]
        )

        print(
            "Constraint adherence:",
            summary["prompt_a"]["constraint_adherence"]
        )

        print(
            "Answer quality:",
            summary["prompt_a"]["answer_quality"]
        )

        print(
            "Overall:",
            summary["prompt_a"]["total"]
        )

        print("\nPrompt B")
        print("-" * 40)

        print(
            "Relevance:",
            summary["prompt_b"]["relevance"]
        )

        print(
            "Groundedness:",
            summary["prompt_b"]["groundedness"]
        )

        print(
            "Constraint adherence:",
            summary["prompt_b"]["constraint_adherence"]
        )

        print(
            "Answer quality:",
            summary["prompt_b"]["answer_quality"]
        )

        print(
            "Overall:",
            summary["prompt_b"]["total"]
        )

        print("\nWins")
        print("-" * 40)

        print(
            "Prompt A:",
            summary["wins"]["A"]
        )

        print(
            "Prompt B:",
            summary["wins"]["B"]
        )

        print(
            "Tie:",
            summary["wins"]["Tie"]
        )

        print("\nBEST PROMPT")
        print("-" * 40)

        print(
            summary["best_prompt"]
        )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    output = {
        "model": MODEL,
        "evaluation_file": str(
            EVALUATION_FILE
        ),
        "summary": summary,
        "results": results
    }

    with open(
        RESULT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nDetailed results saved to:"
        f"\n{RESULT_FILE}"
    )


# ============================================================
# 13. RUN
# ============================================================

if __name__ == "__main__":
    main()