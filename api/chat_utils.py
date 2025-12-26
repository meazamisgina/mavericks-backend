import os
from groq import Groq
from .vector_utils import search_similar_products
from product.models import Product

class ShoppingAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))

    def get_shopping_context(self, query):
        """Finds products relevant to the user's question"""
        # We use a temporary text search or vector search
        # For now, let's grab the latest 5 products as context
        products = Product.objects.all().order_by('-created_at')[:5]
        context = "Current Inventory:\n"
        for p in products:
            context += f"- {p.name}: {p.price} KES, Condition: {p.condition}, Size: {p.size}\n"
        return context

    def ask_agent(self, user_query, user_name="Customer"):
        context = self.get_shopping_context(user_query)
        
        prompt = f"""
        You are 'Maverick AI', a street-smart fashion assistant for a Kenyan thrift marketplace.
        Use this inventory to help the user:
        {context}
        
        User Question: {user_query}
        
        Instructions:
        1. Be friendly and use a bit of Kenyan urban vibe (but stay professional).
        2. If they ask for something not in stock, suggest a Mystery Box.
        3. Keep answers short (max 3 sentences).
        """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

shopping_agent = ShoppingAgent()