import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from core.content_engine import content_engine
from services.social_poster import social_poster
from db.supabase_client import db_client
from config.settings import settings

logger = logging.getLogger(__name__)

generated_images_cache = {}

def is_authorized(update: Update) -> bool:
    user_id = str(update.effective_user.id)
    allowed = [u.strip() for u in settings.ALLOWED_TELEGRAM_USERS.split(',') if u.strip()]
    if not allowed:
        # If not configured, allow access but warn.
        logger.warning(f"ALLOWED_TELEGRAM_USERS is empty! Allowing user {user_id}")
        return True
    
    if user_id in allowed:
        return True
        
    logger.warning(f"Unauthorized access attempt by user {user_id}")
    return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text(f"⛔️ Unauthorized access.\nYour User ID is: `{update.effective_user.id}`\n\nAdd this ID to `ALLOWED_TELEGRAM_USERS` in your `.env` file to gain access.", parse_mode="Markdown")
        return

    await update.message.reply_text(
        "Welcome to AI Content Studio! 🚀\n\n"
        "Commands:\n"
        "/generate - Generate a new post batch\n"
        "/help - Show this message"
    )

async def _do_generate(message_obj, update: Update):
    if not is_authorized(update):
        await message_obj.reply_text(f"⛔️ Unauthorized access.\nYour User ID is: `{update.effective_user.id}`", parse_mode="Markdown")
        return

    msg = await message_obj.reply_text("🔄 Generating content... This might take a minute.")
    
    try:
        post_data = await content_engine.generate_post()
        post_id = post_data["post_id"]
        caption = post_data["caption"]
        images_bytes = post_data["images_bytes"]
        
        generated_images_cache[post_id] = images_bytes
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve & Post to FB + IG", callback_data=f"approve_{post_id}"),
                InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if images_bytes:
            media = [InputMediaPhoto(img) for img in images_bytes]
            await message_obj.reply_media_group(media=media)
            
        await message_obj.reply_text(
            f"**Generated Caption:**\n\n{caption}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Generate failed: {e}")
        await message_obj.reply_text("❌ Failed to generate content. Check logs.")

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _do_generate(update.message, update)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.callback_query.answer("⛔️ Unauthorized access.", show_alert=True)
        return

    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("approve_"):
        post_id = data.split("_")[1]
        await query.edit_message_text("⏳ Uploading images & posting to socials...")
        
        post = db_client.get_pending_post(post_id)
        if not post:
            await query.edit_message_text("❌ Post not found in database or already processed.")
            return
            
        images_bytes = generated_images_cache.get(post_id, [])
        
        try:
            # 1. Upload to Supabase to get public URLs for Instagram
            image_urls = []
            uploaded_files = []
            for i, img_bytes in enumerate(images_bytes):
                file_name = f"{post_id}_{i}.jpg"
                url = db_client.upload_image(file_name, img_bytes)
                image_urls.append(url)
                uploaded_files.append(file_name)
                
            # 2. Post to Facebook (using bytes directly)
            fb_post_id = None
            try:
                fb_post_id = social_poster.post_to_facebook(post['caption'], images_bytes)
            except Exception as e:
                logger.error(f"FB Post Failed: {e}")
                
            # 3. Post to Instagram (using public URLs)
            ig_post_id = None
            try:
                ig_post_id = social_poster.post_to_instagram(post['caption'], image_urls)
            except Exception as e:
                logger.error(f"IG Post Failed: {e}")
                
            if not fb_post_id and not ig_post_id:
                raise Exception("Both Facebook and Instagram posting failed.")
                
            # Update DB with FB ID and the newly generated image URLs
            db_client.update_post_status(post_id, 'posted', fb_post_id)
            # Optionally update the row to save the image URLs
            if image_urls:
                db_client.supabase.table('posts').update({'image_urls': image_urls}).eq('id', post_id).execute()
                
            # Clean up Supabase Storage since the images have been pushed to IG
            if uploaded_files:
                db_client.delete_images(uploaded_files)
                
            generated_images_cache.pop(post_id, None)
            
            success_msg = "✅ Successfully posted!\n"
            if fb_post_id: success_msg += f"- Facebook ID: {fb_post_id}\n"
            if ig_post_id: success_msg += f"- Instagram ID: {ig_post_id}"
                
            await query.edit_message_text(success_msg)
        except Exception as e:
            logger.error(f"Approval post failed: {e}")
            await query.edit_message_text("❌ Failed to post to socials. See logs.")
            
    elif data == "regenerate":
        await query.edit_message_text("🔄 Triggering regeneration...")
        await _do_generate(query.message, update)
