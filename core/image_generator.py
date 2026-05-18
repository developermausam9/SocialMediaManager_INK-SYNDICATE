import logging
import asyncio
from io import BytesIO
from huggingface_hub import InferenceClient
from config.settings import settings

logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self):
        self.api_key = settings.HF_API_KEY
        if self.api_key and self.api_key != 'your_huggingface_key':
            self.client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=self.api_key, timeout=120)
        else:
            self.client = None

    async def generate_single_image(self, prompt: str) -> bytes:
        if not self.client:
            logger.warning("Mocking Image Generation")
            await asyncio.sleep(1)
            transparent_gif = bytes.fromhex("47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b")
            return transparent_gif

        try:
            loop = asyncio.get_event_loop()
            # client.text_to_image runs synchronously, returns a PIL Image
            image = await loop.run_in_executor(
                None,
                lambda: self.client.text_to_image(prompt)
            )
            
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            raise

    async def generate_images(self, prompts: list[str]) -> list[bytes]:
        """Generates multiple images concurrently."""
        tasks = [self.generate_single_image(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_images = []
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Image generation task failed: {res}")
            else:
                valid_images.append(res)
        
        return valid_images

image_generator = ImageGenerator()
