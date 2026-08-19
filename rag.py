# ============================================================
# RAG CONTEXT
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