-- Supabase Schema for Amazon Ads Token Manager
-- This creates the necessary tables for storing OAuth tokens and account information

-- Create accounts table for managing multiple Amazon Ads accounts
CREATE TABLE IF NOT EXISTS amazon_ads_accounts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    client_id VARCHAR(500) NOT NULL,
    client_secret_encrypted TEXT NOT NULL, -- Encrypted in application layer
    redirect_uri VARCHAR(500) DEFAULT 'https://localhost',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create tokens table for storing OAuth tokens
CREATE TABLE IF NOT EXISTS amazon_ads_tokens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES amazon_ads_accounts(id) ON DELETE CASCADE,
    access_token TEXT NOT NULL, -- Encrypted in application layer
    refresh_token TEXT NOT NULL, -- Encrypted in application layer
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_refreshed_at TIMESTAMP WITH TIME ZONE,
    refresh_count INTEGER DEFAULT 0,
    is_valid BOOLEAN DEFAULT true,
    UNIQUE(account_id) -- One active token set per account
);

-- Create token history table for audit trail
CREATE TABLE IF NOT EXISTS token_refresh_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES amazon_ads_accounts(id) ON DELETE CASCADE,
    token_id UUID REFERENCES amazon_ads_tokens(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL, -- 'created', 'refreshed', 'expired', 'revoked'
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create API keys table for service authentication
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- SHA256 hash of the API key
    name VARCHAR(255) NOT NULL,
    account_id UUID REFERENCES amazon_ads_accounts(id) ON DELETE CASCADE,
    permissions JSONB DEFAULT '["read", "write"]'::jsonb,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Create indexes for performance
CREATE INDEX idx_tokens_account_id ON amazon_ads_tokens(account_id);
CREATE INDEX idx_tokens_expires_at ON amazon_ads_tokens(expires_at);
CREATE INDEX idx_tokens_is_valid ON amazon_ads_tokens(is_valid);
CREATE INDEX idx_history_account_id ON token_refresh_history(account_id);
CREATE INDEX idx_history_created_at ON token_refresh_history(created_at);
CREATE INDEX idx_api_keys_account_id ON api_keys(account_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to tables
CREATE TRIGGER update_amazon_ads_accounts_updated_at
    BEFORE UPDATE ON amazon_ads_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_amazon_ads_tokens_updated_at
    BEFORE UPDATE ON amazon_ads_tokens
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    UPDATE amazon_ads_tokens
    SET is_valid = false
    WHERE expires_at < NOW() AND is_valid = true;

    -- Log the expiration
    INSERT INTO token_refresh_history (account_id, token_id, action, success)
    SELECT account_id, id, 'expired', true
    FROM amazon_ads_tokens
    WHERE expires_at < NOW() AND is_valid = true;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get valid token
CREATE OR REPLACE FUNCTION get_valid_token(p_account_id UUID)
RETURNS TABLE (
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    needs_refresh BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.access_token,
        t.refresh_token,
        t.expires_at,
        (t.expires_at <= NOW() + INTERVAL '5 minutes') as needs_refresh
    FROM amazon_ads_tokens t
    WHERE t.account_id = p_account_id
        AND t.is_valid = true
    ORDER BY t.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security Policies
ALTER TABLE amazon_ads_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE amazon_ads_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_refresh_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create policies for service role (full access)
-- Note: The service role key bypasses RLS, so these policies are for anon/authenticated access

-- Accounts table policies (using service role for now, can be adjusted)
CREATE POLICY "Enable all access for service role" ON amazon_ads_accounts
    FOR ALL USING (true);

-- Tokens table policies
CREATE POLICY "Enable all access for service role" ON amazon_ads_tokens
    FOR ALL USING (true);

-- History table policies
CREATE POLICY "Enable all access for service role" ON token_refresh_history
    FOR ALL USING (true);

-- API keys policies
CREATE POLICY "Enable all access for service role" ON api_keys
    FOR ALL USING (true);

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;