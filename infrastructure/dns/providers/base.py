import json
import logging
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import requests


class BaseDNSProvider(ABC):
    name = ""

    @property
    def PATH_STATE_OUTPUT(self) -> Path | None:
        return (
            Path(__file__).absolute().parent.parent / "logs" / f"state_{self.name}.json"
        )

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> dict:
        try:
            self.logger.info("starting DNS provider run")
            res = self._run()
        except Exception as e:
            self.logger.fatal("unexpected error", exc_info=True)
            res = {"success": False, "errors": [f"{e.__class__.__name__}: {e}"]}

        if self.PATH_STATE_OUTPUT:
            self.PATH_STATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            self.PATH_STATE_OUTPUT.write_text(json.dumps(res, indent=2))

        return res

    @abstractmethod
    def _run(self) -> dict:
        pass

    @staticmethod
    @lru_cache
    def get_public_ip() -> str | None:
        try:
            response = requests.get("https://api.ipify.org")
            if response.status_code == 200:
                return response.text
        except requests.RequestException:
            return None

    @staticmethod
    def get_env_var(var: str):
        try:
            return os.environ[var]
        except KeyError:
            raise RuntimeError(f"environment variable not found: {var}")
