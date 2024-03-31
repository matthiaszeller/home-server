import logging
import os

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class APIRoles(BaseModel):
    # Dynamic role names with their permissions
    __root__: dict[str, list[str]] = Field(default_factory=dict)


class TGRoles(BaseModel):
    # Dynamic role names with their permissions
    __root__: dict[str, list[str]] = Field(default_factory=dict)


class PermissionsConfig(BaseModel):
    api_roles: APIRoles = Field(default_factory=APIRoles)
    tg_roles: TGRoles = Field(default_factory=TGRoles)


class AccessControlManager:

    logger = logging.getLogger("AccessControlManager")

    def __init__(self, permissions_config_path: str, secrets_env_path: str) -> None:
        self.logger.debug("Initializing Access Control Manager...")
        load_dotenv(secrets_env_path)
        self._permissions: PermissionsConfig = self._load_permissions(
            permissions_config_path
        )
        # Maps are now directly loaded from environment variables, leveraging Pydantic's parsing
        self._service_users: dict[str, str] = self._load_service_users()
        self._telegram_users: dict[str, str] = self._load_telegram_users()
        self.logger.info("Access Control Manager initialized successfully.")

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
        return {k: v for k, v in os.environ.items() if k.startswith("API_KEY_FOR_")}

    @classmethod
    def _load_telegram_users(cls) -> dict[str, str]:
        """Loads Telegram user mappings from environment variables."""
        cls.logger.info("Loading Telegram user mappings...")
        return {k: v for k, v in os.environ.items() if k.startswith("TELEGRAM_USER_")}

    def check_api_access(self, api_key: str, task: str) -> bool:
        """Checks if a service user identified by an API key has access to the specified task."""
        role = self._service_users.get(api_key)
        if role:
            allowed_endpoints = self._permissions.api_roles.__root__.get(role, [])
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
            allowed_commands = self._permissions.tg_roles.__root__.get(role, [])
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
