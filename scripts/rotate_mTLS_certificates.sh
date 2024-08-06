#!/bin/bash

# Directories for certificates (adjust as necessary)
EDGE_CERT_DIR="infrastructure/nginx_edge/certs"
INTERNAL_CERT_DIR="infrastructure/nginx_internal/certs"

# Backup existing certificates
echo "Backing up existing certificates..."
cp "$EDGE_CERT_DIR/nginxEdge.crt" "$EDGE_CERT_DIR/nginxEdge.crt.bak"
cp "$EDGE_CERT_DIR/nginxEdge.key" "$EDGE_CERT_DIR/nginxEdge.key.bak"
cp "$INTERNAL_CERT_DIR/nginxInternal.crt" "$INTERNAL_CERT_DIR/nginxInternal.crt.bak"
cp "$INTERNAL_CERT_DIR/nginxInternal.key" "$INTERNAL_CERT_DIR/nginxInternal.key.bak"

# Generate new private keys
echo "Generating new private keys..."
openssl genrsa -out "$EDGE_CERT_DIR/nginxEdge.key" 2048
openssl genrsa -out "$INTERNAL_CERT_DIR/nginxInternal.key" 2048

# Generate new CSRs
echo "Generating new CSRs..."
openssl req -new -key "$EDGE_CERT_DIR/nginxEdge.key" -out "$EDGE_CERT_DIR/nginxEdge.csr" -subj "/CN=localhost"
openssl req -new -key "$INTERNAL_CERT_DIR/nginxInternal.key" -out "$INTERNAL_CERT_DIR/nginxInternal.csr" -subj "/CN=host.docker.internal"

# Sign the CSRs with the CA
echo "Signing the CSRs with the CA..."
openssl x509 -req -in "$EDGE_CERT_DIR/nginxEdge.csr" -CA ca.crt -CAkey ca.key -CAcreateserial -out "$EDGE_CERT_DIR/nginxEdge.crt" -days 365 -sha256
openssl x509 -req -in "$INTERNAL_CERT_DIR/nginxInternal.csr" -CA ca.crt -CAkey ca.key -CAcreateserial -out "$INTERNAL_CERT_DIR/nginxInternal.crt" -days 365 -sha256

# Cleanup CSRs
echo "Cleaning up CSRs..."
rm "$EDGE_CERT_DIR/nginxEdge.csr"
rm "$INTERNAL_CERT_DIR/nginxInternal.csr"

# Optional: Restart Nginx services to apply changes
# Uncomment and adjust the following lines according to your setup, if necessary
#echo "Restarting Nginx services..."
#sudo systemctl restart nginx_edge
#sudo systemctl restart nginx_internal

echo "Certificate rotation complete."
