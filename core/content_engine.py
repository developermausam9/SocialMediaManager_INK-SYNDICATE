import logging
from core.decision_engine import DecisionEngine
from core.gemini_client import GeminiClient
from core.image_generator import image_generator
from db.supabase_client import db_client

logger = logging.getLogger(__name__)

class ContentEngine:
    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.gemini_client = GeminiClient()
        self.image_generator = image_generator
        self.db = db_client

    async def generate_post(self) -> dict:
        """
        Runs the full pipeline to generate a post.
        Returns a dict with post_id, category, caption, prompts, and image_bytes.
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 1. Select Category
                category_key, category_desc = self.decision_engine.select_category()
                
                # 2. Generate Content
                content = self.gemini_client.generate_content(category_desc)
                caption = content.get("caption", "")
                prompts = content.get("image_prompts", [])
                
                # 3. Check Duplication
                if self.db.check_duplication(category_key, caption):
                    logger.info("Duplication detected, retrying generation...")
                    continue
                
                # 4. Generate Images
                images_bytes = await self.image_generator.generate_images(prompts)
                
                if not images_bytes:
                    logger.warning("No images generated, retrying...")
                    continue
                
                # Save to DB as pending
                post_id = self.db.save_post(category_key, caption, prompts, [])
                
                return {
                    "post_id": post_id,
                    "category": category_key,
                    "caption": caption,
                    "prompts": prompts,
                    "images_bytes": images_bytes
                }
                
            except Exception as e:
                logger.error(f"Generation attempt {attempt+1} failed: {e}")
                
        raise Exception("Failed to generate content after multiple attempts.")
        
content_engine = ContentEngine()
