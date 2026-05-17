# SYSTEM ARCHITECTURE

## Overview
This system is an AI-driven content automation engine for Facebook marketing and digital poster business.

---

## Flow

1. Telegram bot triggers generation
2. Decision engine selects content category
3. Gemini generates:
   - caption
   - image prompts
4. Image generator creates visuals
5. Bot sends preview
6. User approves or regenerates
7. If approved:
   - Post to Facebook Page
   - Save to Supabase
   - Log history

---

## Components

### Telegram Bot
- Control interface
- Approval system
- Preview system

### Content Engine
- Category selector
- Anti-repetition logic

### Gemini API Layer
- Caption generation
- Prompt generation
- Strategy planning

### Image Generator
- Stable Diffusion / Imagen API
- Generates 3–4 images per request

### Facebook Poster
- Meta Graph API integration
- Posts images + captions

### Database
- Supabase used for:
  - history
  - posts
  - logs