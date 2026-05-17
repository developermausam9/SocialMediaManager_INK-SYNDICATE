import json
import logging
import google.generativeai as genai
from config.settings import settings
from core.prompt_library import SYSTEM_INSTRUCTION

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        if settings.GEMINI_API_KEY != 'your_key':
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=SYSTEM_INSTRUCTION
            )
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not set. Gemini generation will fail or mock.")

    def generate_content(self, category_desc: str) -> dict:
        """Generates caption and 3 image prompts based on design type."""
        if not self.model:
            logger.warning("Mocking Gemini generation")
            return {
                "design_type": "poster",
                "caption": f"Mock caption for {category_desc} #mock #test",
                "image_prompts": [
                    f"Mock print-ready poster layout 1 for {category_desc}",
                    f"Mock print-ready poster layout 2 for {category_desc}",
                    f"Mock print-ready poster layout 3 for {category_desc}"
                ]
            }

        prompt = f"Generate a print marketing post for the following design requirement:\n{category_desc}"
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            data = json.loads(text.strip())
            
            # Quality Filter: Ensure structural / commercial intent
            if "image_prompts" not in data:
                raise ValueError("Missing 'image_prompts' in JSON")
                
            prompts_text = " ".join(data["image_prompts"]).lower()
            valid_keywords = ["layout", "composition", "print", "mockup", "banner", "sticker", "poster", "border", "grid", "typography"]
            
            if not any(keyword in prompts_text for keyword in valid_keywords):
                logger.error("Quality Filter Failed: Prompts lack structural/print intent keywords.")
                raise ValueError("Quality Filter Failed: Output does not resemble commercial print design.")

            return data
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
