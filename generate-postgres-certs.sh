#!/bin/bash
# Generate self-signed SSL certificates for PostgreSQL

echo "🔐 Generating SSL certificates for PostgreSQL encryption..."

# Create directory for certificates
mkdir -p ./postgres-certs

# Generate private key
openssl genrsa -out ./postgres-certs/server.key 2048

# Generate certificate signing request
openssl req -new -key ./postgres-certs/server.key -out ./postgres-certs/server.csr \
  -subj "/C=US/ST=State/L=City/O=DriftGuard/OU=Engineering/CN=postgres"

# Generate self-signed certificate (valid for 10 years)
openssl x509 -req -days 3650 -in ./postgres-certs/server.csr \
  -signkey ./postgres-certs/server.key -out ./postgres-certs/server.crt

# Set proper permissions (PostgreSQL requires strict permissions)
chmod 600 ./postgres-certs/server.key
chmod 644 ./postgres-certs/server.crt

echo "✅ SSL certificates generated successfully!"
echo ""
echo "📁 Certificate files created:"
echo "   - ./postgres-certs/server.key (private key)"
echo "   - ./postgres-certs/server.crt (certificate)"
echo ""
echo "🚀 You can now run: docker-compose up -d"
