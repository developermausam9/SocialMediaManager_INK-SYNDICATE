# AI Content Studio

An automated system that generates viral Facebook content, creates AI images using HuggingFace Inference API, and posts after user approval via Telegram.

## Features
- **Intelligent Category Selection:** Rotates between emotional aesthetic, anime-inspired, mythology, service marketing, and behind-the-scenes content based on defined weights.
- **Anti-Duplication Engine:** Prevents repeating the same category twice in a row, the same visual style in the last 3 posts, and similar captions.
- **Content Generation:** Uses Google Gemini 1.5 Pro to write engaging captions and image generation prompts.
- **Image Generation:** Connects to HuggingFace Inference API (Stable Diffusion XL) to generate print-quality, high-resolution visuals.
- **Telegram Bot:** Full control over generation and approval workflows.
- **Facebook Integration:** Posts text and multiple photos using the Meta Graph API.
- **Supabase Storage:** Logs history and state to prevent duplication.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   - Create a project in [Supabase](https://supabase.com).
   - Run the SQL script located at `db/schema.sql` in your Supabase SQL editor.

3. **Environment Variables**
   - Edit the `.env` file and insert all your API keys:
     - `GEMINI_API_KEY`: Google AI Studio Key
     - `TELEGRAM_BOT_TOKEN`: Telegram BotFather Token
     - `SUPABASE_URL` & `SUPABASE_KEY`: Supabase API details
     - `FB_PAGE_ID` & `FB_ACCESS_TOKEN`: Meta Graph API details
     - `HF_API_KEY`: HuggingFace API Key

4. **Run the System**
   ```bash
   python main.py
   ```

## Usage
Start a chat with your Telegram Bot and use the following commands:
- `/generate`: Create a new content batch. You will receive the images and the caption.
- Click **✅ Approve & Post** to publish to Facebook.
- Click **🔄 Regenerate** to generate a new post instead.
