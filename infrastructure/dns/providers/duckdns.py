import requests

from .base import BaseDNSProvider, DNSUpdateResult

BASE_URL = "https://www.duckdns.org/update"


class DuckDNSProvider(BaseDNSProvider):
    name = "duckdns"

    def _run(self) -> DNSUpdateResult:
        token = self.get_env_var("DUCKDNS_TOKEN")
        domain = self.get_env_var("DUCKDNS_DOMAIN")
        ip = self.get_public_ip()

        params = {
            "domains": domain,
            "token": token,
            "ip": ip,
        }

        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()

        message = response.text
        messages = [] if message.lower().strip() != "ok" else [message]
        errors = [] if messages else [message]

        return DNSUpdateResult(
            ip=ip,
            messages=messages,
            errors=errors,
        )
