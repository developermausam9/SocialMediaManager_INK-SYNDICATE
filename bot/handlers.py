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
                InlineKeyboardButton("🚀 Post to Both (FB + IG)", callback_data=f"approve_both_{post_id}")
            ],
            [
                InlineKeyboardButton("🔵 Post to FB Only", callback_data=f"approve_fb_{post_id}"),
                InlineKeyboardButton("🟣 Post to IG Only", callback_data=f"approve_ig_{post_id}")
            ],
            [
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
        parts = data.split("_")
        if len(parts) == 3:
            target = parts[1] # "both", "fb", or "ig"
            post_id = parts[2]
        else:
            target = "both"
            post_id = parts[1]
            
        target_str = "socials"
        if target == "fb":
            target_str = "Facebook"
        elif target == "ig":
            target_str = "Instagram"
            
        await query.edit_message_text(f"⏳ Uploading images & posting to {target_str}...")
        
        post = db_client.get_pending_post(post_id)
        if not post:
            await query.edit_message_text("❌ Post not found in database or already processed.")
            return
            
        images_bytes = generated_images_cache.get(post_id, [])
        
        try:
            # 1. Upload to Supabase to get public URLs for Instagram (only if IG or Both, and not uploaded already)
            image_urls = []
            uploaded_files = []
            if target in ("both", "ig") and images_bytes:
                for i, img_bytes in enumerate(images_bytes):
                    file_name = f"{post_id}_{i}.jpg"
                    url = db_client.upload_image(file_name, img_bytes)
                    image_urls.append(url)
                    uploaded_files.append(file_name)
                
            # 2. Post to Facebook (using bytes directly, only if FB or Both)
            fb_post_id = None
            if target in ("both", "fb"):
                try:
                    fb_post_id = social_poster.post_to_facebook(post['caption'], images_bytes)
                except Exception as e:
                    logger.error(f"FB Post Failed: {e}")
                    
            # 3. Post to Instagram (using public URLs, only if IG or Both)
            ig_post_id = None
            if target in ("both", "ig"):
                try:
                    ig_post_id = social_poster.post_to_instagram(post['caption'], image_urls)
                except Exception as e:
                    logger.error(f"IG Post Failed: {e}")
                    
            # Determine success status
            fb_success = (target in ("both", "fb") and fb_post_id is not None)
            ig_success = (target in ("both", "ig") and ig_post_id is not None)
            
            # We raise an error only if everything selected failed completely
            if target == "fb" and not fb_success:
                raise Exception("Facebook posting failed.")
            elif target == "ig" and not ig_success:
                raise Exception("Instagram posting failed.")
            elif target == "both" and not fb_success and not ig_success:
                raise Exception("Both Facebook and Instagram posting failed.")
                
            # Update DB with FB ID if Facebook was successful
            if fb_success:
                db_client.update_post_status(post_id, 'posted', fb_post_id)
            
            # Save the image URLs in the DB if Instagram was successful
            if ig_success and image_urls:
                try:
                    db_client.supabase.table('posts').update({'image_urls': image_urls}).eq('id', post_id).execute()
                except Exception as e:
                    logger.error(f"Failed to update image URLs in DB: {e}")
                    
            # Clean up Supabase Storage only if Instagram posting was successful OR if we only posted to Facebook successfully
            if ig_success or (target == "fb" and fb_success):
                if uploaded_files:
                    try:
                        db_client.delete_images(uploaded_files)
                    except Exception as e:
                        logger.error(f"Cleanup of images failed: {e}")
            
            # Clean cache only if the requested targets succeeded completely
            target_succeeded = False
            if target == "fb" and fb_success:
                target_succeeded = True
            elif target == "ig" and ig_success:
                target_succeeded = True
            elif target == "both" and fb_success and ig_success:
                target_succeeded = True
                
            if target_succeeded:
                generated_images_cache.pop(post_id, None)
                
            # Construct feedback message
            success_msg = ""
            if fb_success and ig_success:
                success_msg = f"✅ Successfully posted to both!\n- Facebook ID: {fb_post_id}\n- Instagram ID: {ig_post_id}"
            elif fb_success and target == "fb":
                success_msg = f"✅ Successfully posted to Facebook!\n- Facebook ID: {fb_post_id}"
            elif ig_success and target == "ig":
                success_msg = f"✅ Successfully posted to Instagram!\n- Instagram ID: {ig_post_id}"
            elif target == "both" and fb_success and not ig_success:
                success_msg = f"⚠️ Posted to Facebook, but **failed on Instagram**!\n- Facebook ID: {fb_post_id}\n\n👉 You can fix the issue and click **🟣 Retry IG Only** below to retry!"
            elif target == "both" and not fb_success and ig_success:
                success_msg = f"⚠️ Posted to Instagram, but **failed on Facebook**!\n- Instagram ID: {ig_post_id}\n\n👉 You can fix the issue and click **🔵 Retry FB Only** below to retry!"
            else:
                success_msg = "❌ Posting failed."
                
            # Show retry keyboard if there were partial failures
            if not target_succeeded:
                keyboard = []
                fb_button_needed = (target in ("both", "fb") and not fb_success)
                ig_button_needed = (target in ("both", "ig") and not ig_success)
                
                row = []
                if fb_button_needed:
                    row.append(InlineKeyboardButton("🔵 Retry FB Only", callback_data=f"approve_fb_{post_id}"))
                if ig_button_needed:
                    row.append(InlineKeyboardButton("🟣 Retry IG Only", callback_data=f"approve_ig_{post_id}"))
                    
                if row:
                    keyboard.append(row)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(success_msg, reply_markup=reply_markup)
            else:
                await query.edit_message_text(success_msg)
        except Exception as e:
            logger.error(f"Approval post failed: {e}")
            # If everything failed, allow retrying either
            keyboard = []
            row = []
            if target in ("both", "fb"):
                row.append(InlineKeyboardButton("🔵 Retry FB Only", callback_data=f"approve_fb_{post_id}"))
            if target in ("both", "ig"):
                row.append(InlineKeyboardButton("🟣 Retry IG Only", callback_data=f"approve_ig_{post_id}"))
            
            if row:
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"❌ Failed to post to socials: {e}\n\nChoose an option to retry below:", reply_markup=reply_markup)
            
    elif data == "regenerate":
        await query.edit_message_text("🔄 Triggering regeneration...")
        await _do_generate(query.message, update)
