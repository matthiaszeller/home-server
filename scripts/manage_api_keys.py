import logging
import secrets
from pathlib import Path

import yaml
from simple_term_menu import TerminalMenu

from common import config


class ServiceAPIKeyManager:

    logger = logging.getLogger("ServiceAPIKeyManager")

    def __init__(self):
        self.services_dir = Path(__file__).absolute().parent.parent / "services"
        self.env_file = self._get_path_service("tgbot") / ".env"
        self.permissions_file = (
            self._get_path_service("tgbot") / "config" / "permissions.yaml"
        )
        self.services_info: dict[str, tuple[str, list[str]]] = {}
        self.api_roles: set[str] = set()
        self._load_existing_services()
        self._load_api_roles()

    def _load_api_roles(self):
        with self.permissions_file.open() as file:
            data = yaml.safe_load(file)
            self.api_roles = set(data["api_roles"].keys())

    def _load_existing_services(self):
        services_info = {}
        if not self.env_file.exists():
            self.logger.warning(".env file not found. No services registered.")
            return

        with open(self.env_file) as f:
            for line in f:
                if line.startswith("API_KEY_FOR_"):
                    key, value = line.strip().split("=", 1)
                    api_key, *roles = value.split(",")
                    service_name = key.replace("API_KEY_FOR_", "").lower()
                    services_info[service_name] = (api_key, roles)
        self.services_info = services_info

    def _update_env_file(self):
        with open(self.env_file, "w") as file:
            for service, (api_key, roles) in self.services_info.items():
                roles_str = ",".join(roles)
                file.write(f"API_KEY_FOR_{service.upper()}={api_key},{roles_str}\n")

    def _list_service_options(self) -> tuple[list[str], list[str]]:
        """Generates a list of service options for the interactive menu, indicating registration status."""
        services = [
            path.name
            for path in self.services_dir.iterdir()
            if path.is_dir() and "tgbot" != path.name
        ]
        longest_service_name = (
            max(len(service) for service in services) if services else 0
        )

        service_options = []
        for service in services:
            service_status = (
                "Registered" if service.lower() in self.services_info else "Available"
            )
            formatted_service = (
                f"{service.ljust(longest_service_name)} [{service_status}]"
            )
            service_options.append(formatted_service)

        return service_options, services

    def register_service(self, service_name: str, roles: list[str]):
        api_key = secrets.token_urlsafe(32)  # Generate a new API key
        # Assuming roles are provided or determined through some logic
        self.services_info[service_name.lower()] = (api_key, roles)
        self._update_env_file()
        self._write_api_key_to_file(service_name, api_key)
        self.logger.info(
            f"Service '{service_name}' registered with new API key and roles: {', '.join(roles)}."
        )

    def _get_path_service(self, service_name: str) -> Path:
        return self.services_dir / service_name

    def _get_path_service_api_key(self, service_name: str) -> Path:
        return (
            self._get_path_service(service_name)
            / "config"
            / "secrets"
            / "api_token.txt"
        )

    def rotate_api_key(self, service_name: str):
        """Rotates the API key for an existing service, maintaining its roles."""
        if service_name.lower() in self.services_info:
            api_key = secrets.token_urlsafe(32)  # Generate a new API key
            roles = self.services_info[service_name.lower()][
                1
            ]  # Preserve existing roles
            self.services_info[service_name.lower()] = (api_key, roles)
            self._update_env_file()
            self._write_api_key_to_file(service_name, api_key)
            self.logger.info(
                f"API key for service '{service_name}' has been rotated and associated roles preserved."
            )
        else:
            self.logger.error(
                f"Service '{service_name}' is not registered. Cannot rotate API key."
            )

    def _interactive_choose_roles(self) -> list[str]:
        """Interactive menu to choose roles for a service upon registration."""
        roles_options = list(self.api_roles)
        roles_options.append("Done")
        selected_roles = []
        while True:
            terminal_menu = TerminalMenu(
                roles_options, title="Select roles for the service:"
            )
            selection_index = terminal_menu.show()
            if selection_index is None or selection_index == len(roles_options) - 1:
                break
            selected_roles.append(roles_options[selection_index])
            roles_options.remove(roles_options[selection_index])
        return selected_roles

    def _write_api_key_to_file(self, service_name: str, api_key: str):
        """Writes the generated API key to api_key.txt for the specified service."""
        path_api_key = self._get_path_service_api_key(service_name)
        path_api_key.parent.mkdir(
            parents=True, exist_ok=True
        )  # Ensure the directory exists

        with open(path_api_key, "w") as file:
            file.write(api_key)
        self.logger.info(f"API key for '{service_name}' written to {path_api_key}")

    def interactive_menu(self):
        """Displays an interactive menu to register or rotate API keys for services."""
        service_options, services = self._list_service_options()
        service_options.append("Exit")
        terminal_menu = TerminalMenu(
            service_options,
            title="Select a service to register/rotate API key or exit:",
        )
        selection_index = terminal_menu.show()

        if selection_index is None or selection_index == len(services):
            self.logger.info("Exiting.")
            return

        selected_service = services[selection_index]
        if selected_service.lower() in self.services_info:
            self.rotate_api_key(selected_service)
        else:
            # Example: Assign default roles upon registration
            roles = self._interactive_choose_roles()
            self.register_service(selected_service, roles)

        self.interactive_menu()  # Call again for more actions


if __name__ == "__main__":
    config.setup(__file__, service=False)
    manager = ServiceAPIKeyManager()
    manager.interactive_menu()
