import logging
from pathlib import Path
from urllib.parse import urljoin

import requests

from .base import BaseDNSProvider

BASE_URL = "https://api.cloudflare.com/client/v4/"

logger = logging.getLogger(__name__)

PATH_STATE_OUTPUT = (
    Path(__file__).absolute().parent.parent.joinpath("logs", "state_cloudflare.json")
)


class CloudFlareDNSProvider(BaseDNSProvider):
    name = "cloudflare"

    def get_cloudflare_api_header(self):
        api_token = self.get_env_var("CLOUDFLARE_TOKEN")

        return {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def cloudflare_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict = None,
        raise_error: bool = True,
    ) -> dict:
        def is_error_status(status: int):
            return not (200 <= status <= 229)

        request_fun = getattr(requests, method.lower())
        url = urljoin(BASE_URL, endpoint)
        logger.debug("sending", method, "request to", url)
        response = request_fun(
            url,
            headers=self.get_cloudflare_api_header(),
            json=data,
        )
        response_data = response.json()
        if raise_error and is_error_status(response.status_code):
            raise requests.HTTPError(f'{response_data["errors"]}', response=response)

        return response_data

    def get_cloudflare_zone_id(self) -> str:
        return self.get_env_var("CLOUDFLARE_ZONE_ID")

        # res = cloudflare_api_call("zones", "GET")
        # for zone in res["result"]:
        #     if zone["name"] == domain:
        #         return zone["id"]

        # raise RuntimeError(f"domain {domain} does not exist")

    def get_cloudflare_record_id(self, zone_id: str) -> str:
        """
        Only update the root A record.
        """
        root_domain = self.get_env_var("CLOUDFLARE_ROOT_DOMAIN")
        res = self.cloudflare_api_call(f"zones/{zone_id}/dns_records")
        for record in res["result"]:
            if record["name"] == root_domain:
                return record["id"]

        raise RuntimeError(f"record_id not found for root domain {root_domain}")

    def overwrite_cloudflare_dns_record(
        self, zone_id: str, record_id: str, ip: str, name: str, type: str, proxied: bool
    ):
        return self.cloudflare_api_call(
            f"zones/{zone_id}/dns_records/{record_id}",
            "PUT",
            data={"content": ip, "name": name, "proxied": proxied, "type": type},
        )

    def _run(self) -> dict:
        ip = self.get_public_ip()
        zone_id = self.get_cloudflare_zone_id()
        record_id = self.get_cloudflare_record_id(zone_id)

        res = self.overwrite_cloudflare_dns_record(
            zone_id,
            record_id,
            ip,
            self.get_env_var("CLOUDFLARE_ROOT_DOMAIN"),
            type="A",
            proxied=True,
        )

        return res
