import os
import google.generativeai as genai
import time
from app.config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

class GeminiClient:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt, max_output_tokens=512, temperature=0.0):
        start = time.time()
        resp = self.model.generate_content(prompt)
        text = getattr(resp, "text", str(resp))
        elapsed = int((time.time() - start) * 1000)
        return {"text": text, "llm_time_ms": elapsed}
