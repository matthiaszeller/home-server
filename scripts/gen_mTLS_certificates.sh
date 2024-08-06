#!/bin/bash

# Step 0: Create directories
mkdir infrastructure/nginx_edge/certs
mkdir infrastructure/nginx_internal/certs

# Step 1: Generate the CA's Private Key and Certificate
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.crt -subj "/CN=Custom CA"

# Step 2: Generate Private Keys for Nginx Edge and Nginx Internal
openssl genrsa -out infrastructure/nginx_edge/certs/nginxEdge.key 2048
openssl genrsa -out infrastructure/nginx_internal/certs/nginxInternal.key 2048

# Step 3: Generate CSR for Nginx Edge and Nginx Internal
openssl req -new -key infrastructure/nginx_edge/certs/nginxEdge.key -out infrastructure/nginx_edge/certs/nginxEdge.csr -subj "/CN=localhost"
openssl req -new -key infrastructure/nginx_internal/certs/nginxInternal.key -out infrastructure/nginx_internal/certs/nginxInternal.csr -subj "/CN=host.docker.internal"

# Step 4: Sign the CSRs with the CA's Certificate
openssl x509 -req -in infrastructure/nginx_edge/certs/nginxEdge.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out infrastructure/nginx_edge/certs/nginxEdge.crt -days 365 -sha256
openssl x509 -req -in infrastructure/nginx_internal/certs/nginxInternal.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out infrastructure/nginx_internal/certs/nginxInternal.crt -days 365 -sha256

# Step 5: Cleanup (Optional)
rm infrastructure/nginx_edge/certs/nginxEdge.csr
rm infrastructure/nginx_internal/certs/nginxInternal.csr
