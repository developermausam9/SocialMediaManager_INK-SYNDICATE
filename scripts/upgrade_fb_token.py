import requests
import os
from dotenv import load_dotenv

def upgrade_token():
    print("=== Facebook Token Upgrader ===")
    print("This script upgrades your 1-hour short-lived token to a 60-day long-lived token.")
    print("You need your Facebook App ID and App Secret from the App Dashboard (Settings -> Basic).")
    
    app_id = input("Enter App ID: ").strip()
    app_secret = input("Enter App Secret: ").strip()
    
    load_dotenv()
    short_lived_token = os.environ.get("FB_ACCESS_TOKEN", "").strip()
    
    if not short_lived_token:
        short_lived_token = input("No FB_ACCESS_TOKEN found in .env. Paste short-lived token: ").strip()
        
    url = (
        f"https://graph.facebook.com/v19.0/oauth/access_token"
        f"?grant_type=fb_exchange_token"
        f"&client_id={app_id}"
        f"&client_secret={app_secret}"
        f"&fb_exchange_token={short_lived_token}"
    )
    
    res = requests.get(url)
    data = res.json()
    
    if "access_token" in data:
        long_token = data["access_token"]
        print("\n✅ SUCCESS! Here is your 60-day Long-Lived Token:")
        print("--------------------------------------------------")
        print(long_token)
        print("--------------------------------------------------")
        print("Replace FB_ACCESS_TOKEN in your .env file with this new token.")
        
        # Now get the never-expiring PAGE token
        print("\n⏳ Fetching Never-Expiring Page Token...")
        page_url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={long_token}"
        page_res = requests.get(page_url).json()
        
        if "data" in page_res and len(page_res["data"]) > 0:
            print("\n✅ FOUND PAGE TOKENS (These NEVER expire! Use these instead!):")
            for page in page_res["data"]:
                print(f"- Page: {page['name']} | ID: {page['id']}")
                print(f"  Token: {page['access_token']}\n")
        else:
            print("❌ No pages found for this user, or missing 'pages_show_list' permission.")
            
    else:
        print("\n❌ ERROR:", data.get("error", "Unknown error"))

if __name__ == "__main__":
    upgrade_token()
