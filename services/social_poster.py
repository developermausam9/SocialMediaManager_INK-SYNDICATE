import logging
import time
import requests
from config.settings import settings

logger = logging.getLogger(__name__)

class SocialPoster:
    def __init__(self):
        self.page_id = settings.FB_PAGE_ID
        self.access_token = settings.FB_ACCESS_TOKEN
        self.base_url = f"https://graph.facebook.com/v19.0"
        self.ig_account_id = None
        self._fetch_page_details()

    def _fetch_page_details(self):
        if self.page_id == 'your_page_id' or not self.access_token:
            return
            
        try:
            res = requests.get(
                f"{self.base_url}/{self.page_id}",
                params={
                    "fields": "access_token,instagram_business_account", 
                    "access_token": self.access_token
                }
            )
            data = res.json()
            
            # 1. Auto-Upgrade to Page Token
            if "access_token" in data:
                self.access_token = data["access_token"]
                logger.info("Automatically upgraded User Token to Page Token in memory!")
                
            # 2. Fetch Instagram Account ID
            if "instagram_business_account" in data:
                self.ig_account_id = data["instagram_business_account"]["id"]
                logger.info(f"Successfully linked Instagram Account: {self.ig_account_id}")
            else:
                logger.warning("No linked Instagram business account found for this Facebook Page.")
        except Exception as e:
            logger.error(f"Failed to fetch Page details: {e}")

    def post_to_facebook(self, caption: str, images_bytes: list[bytes]) -> str:
        """Uploads images and posts to Facebook."""
        if self.page_id == 'your_page_id' or not self.access_token:
            logger.warning("Mocking Facebook Poster")
            return "mock-fb-id"
            
        try:
            if not images_bytes:
                res = requests.post(
                    f"{self.base_url}/{self.page_id}/feed",
                    data={"message": caption, "access_token": self.access_token}
                )
                res.raise_for_status()
                return res.json().get("id")

            if len(images_bytes) == 1:
                res = requests.post(
                    f"{self.base_url}/{self.page_id}/photos",
                    data={"caption": caption, "access_token": self.access_token},
                    files={"source": ("image.png", images_bytes[0], "image/png")}
                )
                res.raise_for_status()
                return res.json().get("id")
            else:
                attached_media = []
                for img_bytes in images_bytes:
                    res = requests.post(
                        f"{self.base_url}/{self.page_id}/photos",
                        data={"published": "false", "access_token": self.access_token},
                        files={"source": ("image.png", img_bytes, "image/png")}
                    )
                    res.raise_for_status()
                    photo_id = res.json().get("id")
                    attached_media.append({"media_fbid": photo_id})
                
                res = requests.post(
                    f"{self.base_url}/{self.page_id}/feed",
                    json={
                        "message": caption,
                        "attached_media": attached_media,
                        "access_token": self.access_token
                    }
                )
                res.raise_for_status()
                return res.json().get("id")
        except Exception as e:
            logger.error(f"Failed to post bytes to Facebook: {e}")
            raise

    def _wait_for_container(self, container_id: str, max_retries: int = 10, delay_seconds: int = 3) -> bool:
        """Polls the Instagram media container until its status is FINISHED."""
        for attempt in range(max_retries):
            try:
                res = requests.get(
                    f"{self.base_url}/{container_id}",
                    params={"fields": "status_code,status", "access_token": self.access_token}
                )
                res.raise_for_status()
                data = res.json()
                status_code = data.get("status_code")
                logger.info(f"Container {container_id} status check (attempt {attempt+1}/{max_retries}): {status_code} - {data.get('status')}")
                
                if status_code == "FINISHED":
                    return True
                elif status_code == "ERROR":
                    logger.error(f"Instagram media container processing failed: {data.get('status')}")
                    return False
            except Exception as e:
                logger.warning(f"Error checking container status: {e}")
            
            time.sleep(delay_seconds)
        
        logger.warning(f"Timeout waiting for container {container_id} to be ready.")
        return False

    def post_to_instagram(self, caption: str, image_urls: list[str]) -> str:
        """Publishes to Instagram using public image URLs."""
        if not self.ig_account_id:
            logger.warning("No IG Account ID found. Skipping Instagram post.")
            return None
            
        if not image_urls:
            logger.warning("Instagram requires images. Cannot post text only.")
            return None
            
        # Clean URLs by stripping trailing '?'
        clean_urls = [url.rstrip('?') for url in image_urls]
        logger.info(f"Cleaned Instagram image URLs: {clean_urls}")
            
        try:
            if len(clean_urls) == 1:
                # Single photo post
                res = requests.post(
                    f"{self.base_url}/{self.ig_account_id}/media",
                    data={"image_url": clean_urls[0], "caption": caption, "access_token": self.access_token}
                )
                res.raise_for_status()
                container_id = res.json().get("id")
                
                # Wait for container processing
                self._wait_for_container(container_id)
                
                publish_res = requests.post(
                    f"{self.base_url}/{self.ig_account_id}/media_publish",
                    data={"creation_id": container_id, "access_token": self.access_token}
                )
                publish_res.raise_for_status()
                return publish_res.json().get("id")
            else:
                # Carousel post
                item_ids = []
                for url in clean_urls:
                    res = requests.post(
                        f"{self.base_url}/{self.ig_account_id}/media",
                        data={"image_url": url, "is_carousel_item": "true", "access_token": self.access_token}
                    )
                    res.raise_for_status()
                    item_ids.append(res.json().get("id"))
                
                # Wait for all child item containers to process successfully
                for item_id in item_ids:
                    self._wait_for_container(item_id)
                
                # Create carousel container
                carousel_res = requests.post(
                    f"{self.base_url}/{self.ig_account_id}/media",
                    data={
                        "media_type": "CAROUSEL",
                        "children": ",".join(item_ids),
                        "caption": caption,
                        "access_token": self.access_token
                    }
                )
                carousel_res.raise_for_status()
                carousel_container_id = carousel_res.json().get("id")
                
                # Wait for carousel container to process
                self._wait_for_container(carousel_container_id)
                
                # Publish carousel
                publish_res = requests.post(
                    f"{self.base_url}/{self.ig_account_id}/media_publish",
                    data={"creation_id": carousel_container_id, "access_token": self.access_token}
                )
                publish_res.raise_for_status()
                return publish_res.json().get("id")
        except Exception as e:
            logger.error(f"Failed to post to Instagram: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"IG API Error Response Body: {e.response.text}")
            raise

social_poster = SocialPoster()
