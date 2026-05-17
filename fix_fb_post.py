import requests
from db.supabase_client import db_client
from services.social_poster import social_poster

post_id = '1fa24274-9f89-43e0-8465-02e281b826a6'
post = db_client.supabase.table('posts').select('*').eq('id', post_id).execute().data[0]

caption = post['caption']
urls = [
    f"https://oziibbgijcbkvgnnxpsj.supabase.co/storage/v1/object/public/ig_images/{post_id}_0.png",
    f"https://oziibbgijcbkvgnnxpsj.supabase.co/storage/v1/object/public/ig_images/{post_id}_1.png",
    f"https://oziibbgijcbkvgnnxpsj.supabase.co/storage/v1/object/public/ig_images/{post_id}_2.png"
]

images_bytes = []
for url in urls:
    res = requests.get(url)
    if res.status_code == 200:
        images_bytes.append(res.content)

if images_bytes:
    print(f"Downloaded {len(images_bytes)} images from Supabase. Posting to FB...")
    fb_id = social_poster.post_to_facebook(caption, images_bytes)
    print(f"Success! FB ID: {fb_id}")
    db_client.update_post_status(post_id, 'posted', fb_id)
else:
    print("Failed to download images.")
