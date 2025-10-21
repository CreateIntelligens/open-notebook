#!/bin/bash
# Auto-generate self-signed SSL certificate if not exists

SSL_DIR="/app/ssl"
SSL_CERT="$SSL_DIR/ssl-cert.pem"
SSL_KEY="$SSL_DIR/ssl-key.pem"

# Create ssl directory if not exists
mkdir -p "$SSL_DIR"

# Generate certificate only if it doesn't exist
if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "Generating self-signed SSL certificate..."

    # Get hostname/IP for certificate
    CERT_HOST="${SSL_CERT_HOST:-localhost}"

    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_KEY" \
        -out "$SSL_CERT" \
        -subj "/C=TW/ST=Taiwan/L=Taipei/O=Open Notebook/OU=Dev/CN=$CERT_HOST" \
        2>/dev/null

    echo "SSL certificate generated for: $CERT_HOST"
    echo "Certificate: $SSL_CERT"
    echo "Private Key: $SSL_KEY"
else
    echo "SSL certificate already exists, skipping generation"
fi
