import requests

from .base import BaseDNSProvider

BASE_URL = "https://www.duckdns.org/update"


class DuckDNSProvider(BaseDNSProvider):
    name = "duckdns"

    def _run(self) -> dict:
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

        return {
            "success": True,
            "ip": ip,
            "message": response.text.strip(),
            "errors": [],
        }
