import asyncio
import os
import requests
from dotenv import load_dotenv

load_dotenv()
page_id = os.environ.get("FB_PAGE_ID")
access_token = os.environ.get("FB_ACCESS_TOKEN")

base_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
img_bytes = bytes.fromhex("47494638396101000100800000ffffff00000021f90401000000002c00000000010001000002024401003b")

res = requests.post(
    base_url,
    data={"published": "false", "access_token": access_token},
    files={"source": ("image.png", img_bytes, "image/png")}
)

print(res.status_code)
print(res.text)
