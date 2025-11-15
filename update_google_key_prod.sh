#!/bin/bash
# Script to update Google API key in production database

echo "🔑 Updating Google API key in production..."

# Database connection details
DB_HOST="driftguard_mvp_db"
DB_USER="myuser"
DB_PASS="mypassword"
DB_NAME="mydatabase"

# Google API key (replace with real key)
GOOGLE_API_KEY="your-real-google-api-key-here"

# SQL to update the Google provider
SQL="
UPDATE provider_configs
SET api_key_encrypted = (
    SELECT encode(
        encrypt(
            '$GOOGLE_API_KEY'::bytea,
            (SELECT secret FROM encryption_keys LIMIT 1)::bytea,
            'aes'::text
        ),
        'hex'
    )
)
WHERE provider = 'google';
"

echo "Connecting to database..."
psql "postgresql://$DB_USER:$DB_PASS@$DB_HOST:5432/$DB_NAME" -c "$SQL"

if [ $? -eq 0 ]; then
    echo "✅ Google API key updated successfully!"
else
    echo "❌ Failed to update Google API key"
fi