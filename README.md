# Home Server

The Home Server setup adopts a refined two-tier Docker stack architecture with dual Nginx instances to enhance security and flexibility. Nginx A serves as the edge-facing reverse proxy for secure external communications, while Nginx B handles internal SSL termination and forwards requests to the rootless Docker stack. This document outlines the updated setup and configuration process, emphasizing the new communication flow, security considerations, and development guidelines.


## Overview of Design

### Security Considerations

#### Secure Communications
- **SSL for External Communication (Nginx A)**: Utilizes SSL certificates from known CAs (e.g., Let's Encrypt) for secure communications between Nginx A and the end-users, ensuring data confidentiality and integrity.
- **Internal Communication**:
  - **mTLS between Nginx A and Nginx B**: Implements Mutual TLS (mTLS) for secure internal communication between the two Nginx instances, ensuring both parties authenticate each other.
  - Communication between Nginx B and services occurs within a Docker bridge network, without SSL, relying on Docker's network isolation for security.


#### User Identity Management
- **Authentication via Vouch**: User identity is enforced through a Vouch whitelist, along with the forwarding of user identity information contained within the `X-Vouch-Idp-Token` header by Nginx to the application.
- **Token Verification**: Applications can verify user identity by parsing the `X-Vouch-Idp-Token`, which follows the format `<base64-header>.<base64-payload>.<base64-signature>`.


## Getting Started

### Setup Components

#### Reverse Proxy Configuration
- **Nginx A**: Acts as the edge-facing reverse proxy, handling SSL/TLS for external communications. SSL certificates from recognized CAs should be configured here.
- **Vouch**: Serves as the middleware handling authentication. Configuration files are located at `config/vouch/config.yaml`.
- **Nginx B**: Positioned between Nginx A and the internal services, Nginx B terminates the SSL connection from Nginx A (using mTLS) and forwards requests to the appropriate services within the Docker network. Here, self-signed certificates or certificates from a private CA can be utilized for mTLS.
- **Auth0 Authorization Configuration**:
   - Navigate to your application settings on your [Auth0 Dashboard](https://manage.auth0.com).
   - Under the `Connections` tab, disable `Username-Password-Authentication` and enable `google-oauth2`.
   - Create an admin role under `User Management/Roles` and assign users accordingly in `User Management/Users`.


### Configuration Steps

1. **Nginx A SSL Configuration**: Configure Nginx A with SSL certificates obtained from a recognized CA to secure communications with end users.

2. **Setting up mTLS between Nginx A and Nginx B**:
   - Generate self-signed certificates or use certificates from a private CA for both Nginx A and Nginx B to establish a trusted mTLS connection.
   - Update Nginx A's configuration to require client certificates for connections to Nginx B, specifying paths to the server's certificate, its private key, and the CA certificate.
   - Configure Nginx B to trust Nginx A's certificate and to present its own certificate to Nginx A during the SSL handshake.

3. **Vouch Configuration with Auth0**: Adjust the Vouch configuration file to include your specific settings and secrets as shown in the provided YAML structure. This setup integrates with Auth0 for authentication. A template file is in `config/vouch/config-template.yaml`.

### Configuring mTLS between Nginx and Services

1. **Generate Certificates**: Follow the steps to generate CA, Nginx, and service certificates.
   1. CA certificate
        ```shell
        # generate CA private key
        openssl genrsa -out ca.key 2048
        # generate CA certificate
        openssl req -x509 -new -nodes -key ca.key -sha256 -days 1024 -out ca.crt
        ```
   2. Server Certificate for nginx:
        ```shell
        # private key for nginx
        openssl genrsa -out nginx.key 2048
        # CSR for nginx
        openssl req -new -key nginx.key -out nginx.csr
        # sign CSR with CA
        openssl x509 -req -in nginx.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out nginx.crt -days 365 -sha256
        ```
   3. Client certificate
        ```shell
        # private key for service
        openssl genrsa -out service.key 2048
        # CSR for service
        openssl req -new -key service.key -out service.csr
        # sign CSR with CA
        openssl x509 -req -in service.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out service.crt -days 365 -sha256
        ```
2. **Configure Nginx for mTLS**: Update the nginx configuration to require client certificates for secure locations, specifying paths to the server's certificate, its private key, and the CA certificate.
    ```
        location /protected/myservice {
            ssl_verify_client on; # Require a valid client certificate
            rewrite ^/protected/myservice(.*) /$1 break;
            proxy_pass http://myservice:5000; # Adjust as necessary
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            # Ensure the proxy forwards the client cert for validation
            proxy_set_header X-Client-Verify $ssl_client_verify;
            proxy_set_header X-Client-DN $ssl_client_s_dn;
            proxy_set_header X-Client-Cert $ssl_client_cert;
            include /etc/nginx/conf.d/common-headers.conf;
        }
    ```
3. **Service Configuration**: Ensure your services are configured to present their client certificates when communicating with Nginx. For Python services, include the necessary certificate paths in your service's HTTP client calls.


### Adding New Services

For adding a new Python-based service, follow these steps:

1. **Service Directory**: create a directory `services/myservice`, containing:
   * `src/` directory
   * `config/` directory
   * `Dockerfile`
       ```dockerfile
        FROM python:3.11-slim

        WORKDIR /app

        COPY ./services/<myservice> .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY ./common ./common
        COPY ./config/* ./config


        ENTRYPOINT ["tail", "-f", "/dev/null"]
        ```
   * `main.py`, which must start with

       ```python
        from common.config import setup
        setup(__file__)
        ```
     this enables using shared python modules (in `/common`)

2. **Docker Compose**: update `docker-compose-rootless.yaml`

## Local Testing and Debugging

For testing services locally, execute them as Python package:
```shell
python -m services.<service_name>.main
```

# TODO

- incorporate in the readme instructions for setting up mTLS between nginx_internal and nginx_edge:
```shell
# Generate the certificate for Nginx Edge with "localhost" as the CN
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout infrastructure/nginx_edge/certs/nginxEdge.key \
-out infrastructure/nginx_edge/certs/nginxEdge.crt \
-subj "/CN=localhost"

# Generate the certificate for Nginx Internal with "host.docker.internal" as the CN
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
-keyout infrastructure/nginx_internal/certs/nginxInternal.key \
-out infrastructure/nginx_internal/certs/nginxInternal.crt \
-subj "/CN=host.docker.internal"
```

- add instructions for nginx SSL certificates with certbot & letsencrypt:
    - `sudo ln -s /etc/letsencrypt/live/<mydomain>/fullchain.pem infrastructure/nginx_edge/certs/fullchain.pem`
    - `sudo ln -s /etc/letsencrypt/live/<mydomain>/privkey.pem infrastructure/nginx_edge/certs/privkey.pem`


## Troubleshooting

### Connectivity and Firewall

Exposing ports within docker compose should bypass UFW rules.
However, `nginx_edge` needs to access host net to forward requests to `nginx_internal`, 
and for that it needs the `host.docker.internal`.
In my case, I had to **enable port 8443 on UFW** for enabling such inter-nginx communication.


## Deployment on RaspberryPi

#### Docker stats & Memory usage

If `docker stats` doesn't show any memory usage (0.0%), according to [this post](https://stackoverflow.com/questions/45541242/docker-stats-shows-zero-memory-usage-even-for-running-containers), simply add to `/boot/firmware/cmdline.txt`:
```
cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1
```
