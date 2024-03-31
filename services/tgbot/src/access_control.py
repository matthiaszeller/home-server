import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, RootModel


class BaseRole(RootModel):
    root: dict[str, list[str]]

    def __getitem__(self, key: str) -> list[str]:
        return self.root[key]

    def get(self, key: str, default=None) -> list[str]:
        return self.root.get(key, default)


APIRoles = BaseRole
TGRoles = BaseRole


class PermissionsConfig(BaseModel):
    api_roles: APIRoles = Field(default_factory=APIRoles)
    tg_roles: TGRoles = Field(default_factory=TGRoles)


class AccessControlManager:

    logger = logging.getLogger("AccessControlManager")

    def __init__(self, path_permissions: str | Path, path_dotenv: str | Path) -> None:
        self.logger.debug("Initializing Access Control Manager...")
        load_dotenv(path_dotenv)
        self._permissions: PermissionsConfig = self._load_permissions(path_permissions)
        # Maps are now directly loaded from environment variables, leveraging Pydantic's parsing
        self._service_users: dict[str, str] = self._load_service_users()
        self._telegram_users: dict[str, str] = self._load_telegram_users()
        self.logger.info("Access Control Manager initialized successfully.")
        self.logger.info(f"API roles: {self._permissions.api_roles}")
        self.logger.info(f"Telegram roles: {self._permissions.tg_roles}")
        self.logger.info(f"Service users: {self._service_users.keys()}")
        self.logger.info(f"Telegram users: {self._telegram_users.keys()}")

    @classmethod
    def _load_permissions(cls, file_path: str) -> PermissionsConfig:
        """Loads and validates the permissions configuration."""
        try:
            with open(file_path, "r") as file:
                data = yaml.safe_load(file)
            return PermissionsConfig(**data)
        except FileNotFoundError:
            cls.logger.error(f"Permissions file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            raise Exception(f"Error parsing YAML: {e}")

    @classmethod
    def _load_service_users(cls) -> dict[str, str]:
        """Loads service user mappings from environment variables."""
        cls.logger.debug("Loading service user mappings...")
        return {v: k for k, v in os.environ.items() if k.startswith("API_KEY_FOR_")}

    @classmethod
    def _load_telegram_users(cls) -> dict[str, str]:
        """Loads Telegram user mappings from environment variables."""
        cls.logger.info("Loading Telegram user mappings...")
        return {k: v for k, v in os.environ.items() if k.startswith("TELEGRAM_USER_")}

    def is_token_registered(self, api_key: str) -> bool:
        """Checks if an API key is registered, ignoring specific task permissions."""
        if api_key in self._service_users:
            self.logger.info(f"API key is registered: {self._service_users[api_key]}")
            return True
        self.logger.warning(f"API key not registered: {api_key}")
        return False

    def check_api_access(self, api_key: str, task: str) -> bool:
        """Checks if a service user identified by an API key has access to the specified task."""
        role = self._service_users.get(api_key)
        if role:
            allowed_endpoints = self._permissions.api_roles.get(role, [])
            access_granted = task in allowed_endpoints or "*" in allowed_endpoints
            self.logger.info(
                f"API access {'granted' if access_granted else 'denied'} for key: {api_key}, task: {task}"
            )
            return access_granted
        self.logger.warning(f"API key not found or has no role assigned: {api_key}")
        return False

    def check_tg_command_access(self, user_id: str, command: str) -> bool:
        """Checks if a Telegram user has access to the specified command."""
        role = self._telegram_users.get(f"TELEGRAM_USER_{user_id}")
        if role:
            allowed_commands = self._permissions.tg_roles.get(role, [])
            access_granted = command in allowed_commands or "*" in allowed_commands
            self.logger.info(
                f"Telegram command access {'granted' if access_granted else 'denied'} "
                f"for user: {user_id}, command: {command}"
            )
            return access_granted
        self.logger.warning(
            f"Telegram user ID not found or has no role assigned: {user_id}"
        )
        return False
