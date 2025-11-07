#!/bin/bash
# PostgreSQL initialization script to set up SSL certificates with correct permissions

set -e

# Copy certificates to PostgreSQL data directory and set permissions
cp /var/lib/postgresql/server.crt /var/lib/postgresql/data/server.crt
cp /var/lib/postgresql/server.key /var/lib/postgresql/data/server.key

# Set correct ownership and permissions
chown postgres:postgres /var/lib/postgresql/data/server.crt
chown postgres:postgres /var/lib/postgresql/data/server.key
chmod 600 /var/lib/postgresql/data/server.key
chmod 644 /var/lib/postgresql/data/server.crt

echo "✅ SSL certificates configured successfully"
