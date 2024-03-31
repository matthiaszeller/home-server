from urllib.parse import urljoin

import requests

from .config import PathRegistry as PR
from .config import ServiceRegistry
from .utils import read_text_file


class BaseAPI:
    HOST = "localhost"
    PORT = 5000
    PROTOCOL = "https"

    TIMEOUT = 5  # Timeout for requests, in seconds

    TOKEN: str = read_text_file(PR.get_config_file("secrets/api_token.txt"))

    @classmethod
    def _get_headers(cls) -> dict:
        """Prepare the authorization headers."""
        return {
            "Authorization": f"Bearer {cls.TOKEN}",
            "Content-Type": "application/json",
        }

    @classmethod
    def get_url(cls, endpoint: str) -> str:
        """Get the full URL for the specified endpoint."""
        return urljoin(f"{cls.PROTOCOL}://{cls.HOST}:{cls.PORT}/", endpoint)

    @classmethod
    def post(cls, endpoint: str, data: dict, verify: bool = True) -> requests.Response:
        """Send a POST request to the specified endpoint."""
        url = cls.get_url(endpoint)
        headers = cls._get_headers()
        return requests.post(
            url, json=data, headers=headers, timeout=cls.TIMEOUT, verify=verify
        )

    @classmethod
    def get(cls, endpoint: str, params: dict, verify: bool = True) -> requests.Response:
        """Send a GET request to the specified endpoint."""
        url = cls.get_url(endpoint)
        headers = cls._get_headers()
        return requests.get(
            url, params=params, headers=headers, timeout=cls.TIMEOUT, verify=verify
        )


class TgbotAPI(BaseAPI):

    HOST = ServiceRegistry.get_service_hostname("tgbot")
    PORT = ServiceRegistry.SERVICE_TGBOT_PORT
