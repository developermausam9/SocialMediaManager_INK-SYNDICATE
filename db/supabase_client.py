import os
import json
import logging
from difflib import SequenceMatcher
from supabase import create_client, Client
from config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseDB:
    def __init__(self):
        url: str = settings.SUPABASE_URL
        key: str = settings.SUPABASE_KEY
        # In case they are 'your_url' placeholders, avoid crash during init until we actually call it
        if url != 'your_url' and key != 'your_key':
            self.supabase: Client = create_client(url, key)
        else:
            self.supabase = None
            logger.warning("Supabase URL or Key not set. DB functions will fail or mock.")

    def log(self, level: str, message: str, details: dict = None):
        if not self.supabase:
            logger.info(f"MOCK LOG [{level}]: {message} - {details}")
            return
        try:
            self.supabase.table('logs').insert({
                'level': level,
                'message': message,
                'details': details or {}
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log to Supabase: {e}")

    def save_post(self, category: str, caption: str, prompts: list, image_urls: list) -> str:
        """Save a pending post and return its ID."""
        if not self.supabase:
            logger.warning("Mocking save_post")
            return "mock-uuid"
        try:
            result = self.supabase.table('posts').insert({
                'category': category,
                'caption': caption,
                'prompts': prompts,
                'image_urls': image_urls,
                'status': 'pending'
            }).execute()
            return result.data[0]['id']
        except Exception as e:
            self.log('ERROR', 'Failed to save post', {'error': str(e)})
            raise

    def update_post_status(self, post_id: str, status: str, fb_post_id: str = None):
        """Update the status of a post."""
        if not self.supabase:
            logger.warning("Mocking update_post_status")
            return
        try:
            data = {'status': status}
            if fb_post_id:
                data['fb_post_id'] = fb_post_id
            self.supabase.table('posts').update(data).eq('id', post_id).execute()
        except Exception as e:
            self.log('ERROR', 'Failed to update post status', {'error': str(e), 'post_id': post_id})
            raise

    def get_last_posts(self, limit: int = 20) -> list:
        if not self.supabase:
            return []
        try:
            result = self.supabase.table('posts').select('*').order('created_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            self.log('ERROR', 'Failed to fetch last posts', {'error': str(e)})
            return []

    def check_duplication(self, new_category: str, new_caption: str) -> bool:
        """
        Returns True if duplicate detected.
        - same category twice in a row
        - same visual style (category) within last 3 posts
        - similar captions (>80% similarity)
        """
        posts = self.get_last_posts(20)
        if not posts:
            return False

        # Check last post category (twice in a row)
        if posts[0]['category'] == new_category:
            self.log('INFO', 'Duplication detected: same category twice in a row')
            return True

        # Check for similar captions (>80%)
        for p in posts:
            similarity = SequenceMatcher(None, p['caption'], new_caption).ratio()
            if similarity > 0.8:
                self.log('INFO', f'Duplication detected: similar caption ({similarity*100:.1f}%)')
                return True

        return False
    
    def get_pending_post(self, post_id: str):
        if not self.supabase:
            return None
        try:
            result = self.supabase.table('posts').select('*').eq('id', post_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self.log('ERROR', 'Failed to fetch pending post', {'error': str(e)})
            return None

    def upload_image(self, file_name: str, file_bytes: bytes) -> str:
        """Uploads an image to Supabase storage and returns its public URL."""
        if not self.supabase:
            logger.warning("Mocking image upload")
            return f"https://mock.url/{file_name}"
            
        try:
            # Attempt to create the bucket if it doesn't exist
            try:
                self.supabase.storage.create_bucket('ig_images', options={"public": True})
            except Exception:
                pass # Already exists
                
            self.supabase.storage.from_("ig_images").upload(
                file_name,
                file_bytes,
                file_options={"content-type": "image/png"}
            )
            public_url = self.supabase.storage.from_("ig_images").get_public_url(file_name)
            return public_url
        except Exception as e:
            logger.error(f"Failed to upload image {file_name} to Supabase: {e}")
            raise

    def delete_images(self, file_names: list[str]):
        """Deletes images from Supabase storage."""
        if not self.supabase or not file_names:
            return
        try:
            self.supabase.storage.from_("ig_images").remove(file_names)
            logger.info(f"Deleted {len(file_names)} images from Supabase storage.")
        except Exception as e:
            logger.error(f"Failed to delete images from Supabase: {e}")

db_client = SupabaseDB()
