-- Simple Supabase Migration for Amazon Ads Token Manager
-- Run this in your Supabase SQL Editor

-- 1. Create accounts table
CREATE TABLE IF NOT EXISTS amazon_ads_accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    client_id VARCHAR(500) NOT NULL,
    client_secret_encrypted TEXT NOT NULL,
    redirect_uri VARCHAR(500) DEFAULT 'https://localhost',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 2. Create tokens table
CREATE TABLE IF NOT EXISTS amazon_ads_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES amazon_ads_accounts(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_refreshed_at TIMESTAMP WITH TIME ZONE,
    refresh_count INTEGER DEFAULT 0,
    is_valid BOOLEAN DEFAULT true,
    UNIQUE(account_id)
);

-- 3. Create history table
CREATE TABLE IF NOT EXISTS token_refresh_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES amazon_ads_accounts(id) ON DELETE CASCADE,
    token_id UUID REFERENCES amazon_ads_tokens(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 4. Create API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    account_id UUID REFERENCES amazon_ads_accounts(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '["read", "write"]'::jsonb,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- 5. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tokens_account_id ON amazon_ads_tokens(account_id);
CREATE INDEX IF NOT EXISTS idx_tokens_expires_at ON amazon_ads_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_tokens_is_valid ON amazon_ads_tokens(is_valid);
CREATE INDEX IF NOT EXISTS idx_history_account_id ON token_refresh_history(account_id);
CREATE INDEX IF NOT EXISTS idx_history_created_at ON token_refresh_history(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_account_id ON api_keys(account_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);

-- 6. Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 7. Apply updated_at triggers
DROP TRIGGER IF EXISTS update_amazon_ads_accounts_updated_at ON amazon_ads_accounts;
CREATE TRIGGER update_amazon_ads_accounts_updated_at
    BEFORE UPDATE ON amazon_ads_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_amazon_ads_tokens_updated_at ON amazon_ads_tokens;
CREATE TRIGGER update_amazon_ads_tokens_updated_at
    BEFORE UPDATE ON amazon_ads_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 8. Enable Row Level Security (but with permissive policies for now)
ALTER TABLE amazon_ads_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE amazon_ads_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_refresh_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- 9. Create permissive policies (allows access through service key)
-- You can make these more restrictive later based on your auth needs

DROP POLICY IF EXISTS "Allow all operations on accounts" ON amazon_ads_accounts;
CREATE POLICY "Allow all operations on accounts" ON amazon_ads_accounts
    FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on tokens" ON amazon_ads_tokens;
CREATE POLICY "Allow all operations on tokens" ON amazon_ads_tokens
    FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on history" ON token_refresh_history;
CREATE POLICY "Allow all operations on history" ON token_refresh_history
    FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all operations on api_keys" ON api_keys;
CREATE POLICY "Allow all operations on api_keys" ON api_keys
    FOR ALL USING (true);

-- 10. Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Amazon Ads Token Manager schema created successfully!';
    RAISE NOTICE 'Tables created: amazon_ads_accounts, amazon_ads_tokens, token_refresh_history, api_keys';
    RAISE NOTICE 'Row Level Security enabled with permissive policies';
    RAISE NOTICE 'You can now use the application with your service role key';
END $$;