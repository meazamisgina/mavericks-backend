import os
import json
import base64
from groq import Groq
from django.conf import settings

class GroqAI:
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        self.client = Groq(api_key=api_key)

    def analyze_product_image(self, image_path):
        if not os.path.exists(image_path):
            print(f"AI_DEBUG: File not found at {image_path}")
            return None
            
        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            response = self.client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": (
                                    "You are a fashion expert for a secondhand marketplace. Analyze this image. "
                                    "Return ONLY a JSON object with these exact keys: "
                                    "1. product_name: A catchy 3-word name. "
                                    "2. description: 2 stylish sentences. "
                                    "3. category: The type of clothing (e.g., Jacket). "
                                    "4. audience: Men, Women, or Unisex. "
                                    "5. size: Estimate size (S, M, L, XL, or Free Size). "
                                    "6. condition: Premium, Good, or Thrift. "
                                    "7. condition_notes: Note defects like holes/stains or 'No defects'. "
                                    "Format: {"
                                    "\"product_name\": \"...\", \"description\": \"...\", \"category\": \"...\", "
                                    "\"audience\": \"...\", \"size\": \"...\", \"condition\": \"...\", "
                                    "\"condition_notes\": \"...\""
                                    "}"
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            raw_text = response.choices[0].message.content
            print(f"AI_DEBUG: Groq Response -> {raw_text}")
            return json.loads(raw_text)

        except Exception as e:
            print(f"AI_DEBUG: Groq Error -> {str(e)}")
            return None

ai_brain = GroqAI()