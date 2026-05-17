import os, requests
from dotenv import load_dotenv

load_dotenv()
page_id = os.environ.get("FB_PAGE_ID")
token = os.environ.get("FB_ACCESS_TOKEN")

res = requests.post(
    f"https://graph.facebook.com/v19.0/{page_id}/feed",
    data={"message": "Test post from API", "access_token": token}
)

print(res.status_code)
print(res.json())
