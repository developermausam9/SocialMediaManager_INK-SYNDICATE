-- Supabase Schema for AI Content Studio

CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(255) NOT NULL,
    caption TEXT NOT NULL,
    prompts JSONB NOT NULL,
    image_urls JSONB, -- list of strings/urls
    status VARCHAR(50) DEFAULT 'pending', -- pending, approved, posted, rejected
    fb_post_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(50),
    message TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
