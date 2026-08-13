def create_product_text(product):
    return f"""
    Category: {product['Category']}
    Brand: {product['brand']}
    Model: {product['model']}
    Colour: {product['colour']}
    Product Description: {product['product description']}
    Price: {product['price in INR']} INR
    Rating: {product['rating']}
    """.strip()