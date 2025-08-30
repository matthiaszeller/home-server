import logging
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, ConfigDict, Field


class DNSUpdateResult(BaseModel):
    ip: str | None
    success: bool | None = None
    messages: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    result: Any = None

    model_config = ConfigDict(extra="allow")

    @property
    def is_successful(self) -> bool:
        if self.success is not None:
            return self.success and self.ip is not None and len(self.errors) == 0

        return self.ip is not None and len(self.errors) == 0


class BaseDNSProvider(ABC):
    name = ""

    @property
    def PATH_STATE_OUTPUT(self) -> Path | None:
        return (
            Path(__file__).absolute().parent.parent / "logs" / f"state_{self.name}.json"
        )

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self) -> DNSUpdateResult:
        try:
            self.logger.info("starting DNS provider run")
            res = self._run()
        except Exception as e:
            self.logger.fatal("unexpected error", exc_info=True)
            res = DNSUpdateResult(
                success=False,
                ip=self.get_public_ip(),
                errors=[f"{e.__class__.__name__}: {e}"],
            )

        if p := self.PATH_STATE_OUTPUT:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(res.model_dump_json(indent=2))

        return res

    @abstractmethod
    def _run(self) -> DNSUpdateResult:
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
