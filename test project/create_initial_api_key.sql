-- Create Initial API Key for Web Interface
-- Run this in Supabase SQL Editor after the main migration

-- Generate a simple API key (you should change this to something more secure)
-- This is just for initial setup
DO $$
DECLARE
    api_key_plain TEXT := 'amzn_ads_initial_setup_key_2024_change_this';
    key_hash TEXT;
BEGIN
    -- Create SHA256 hash of the API key
    key_hash := encode(digest(api_key_plain, 'sha256'), 'hex');

    -- Insert the API key
    INSERT INTO api_keys (
        key_hash,
        name,
        permissions,
        is_active,
        created_at
    ) VALUES (
        key_hash,
        'Initial Setup Key',
        '["read", "write", "web", "admin"]'::jsonb,
        true,
        NOW()
    ) ON CONFLICT (key_hash) DO NOTHING;

    RAISE NOTICE '✅ API Key created successfully!';
    RAISE NOTICE '🔑 Your API Key: %', api_key_plain;
    RAISE NOTICE '⚠️  IMPORTANT: Save this key securely and change it in production!';
END $$;

-- Verify the key was created
SELECT
    name,
    permissions,
    created_at,
    is_active
FROM api_keys
WHERE name = 'Initial Setup Key';

-- Show total API keys
SELECT COUNT(*) as total_api_keys FROM api_keys;