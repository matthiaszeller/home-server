import logging
import secrets
from pathlib import Path

from simple_term_menu import TerminalMenu

from common import config


class ServiceAPIKeyManager:

    logger = logging.getLogger("ServiceAPIKeyManager")

    def __init__(self):
        self.services_dir = Path(__file__).absolute().parent.parent / "services"
        env_file = self._get_path_service("tgbot") / ".env"
        self.env_file = Path(env_file)
        self._load_existing_services()

    def _load_existing_services(self):
        if self.env_file.exists():
            with open(self.env_file) as f:
                self.existing_services = [line.split("=")[0] for line in f.readlines()]
        else:
            self.existing_services = []

    def _list_service_options(self):
        """Lists services with their registration status, aligned using Python's format."""
        services = [
            path.name
            for path in self.services_dir.iterdir()
            if path.is_dir() and "tgbot" != path.name
        ]
        longest_service_name = max(services, key=len)
        service_options = []

        for service in services:
            service_key = f"API_KEY_FOR_{service.upper()}"
            status = (
                "Registered" if service_key in self.existing_services else "Available"
            )
            formatted_service = f"{service.ljust(len(longest_service_name))} [{status}]"
            service_options.append(formatted_service)

        return service_options, services

    def register_service(self, service_name: str):
        """Registers or rotates a service API key."""
        if f"API_KEY_FOR_{service_name.upper()}" in self.existing_services:
            self.rotate_api_key(service_name)
        else:
            self._create_api_key(service_name)
            self.logger.info(
                f"Service '{service_name}' registered successfully with API key."
            )
        # reload the list of services after registration
        self._load_existing_services()

    def _get_path_service(self, service_name: str) -> Path:
        return self.services_dir / service_name

    def _get_path_service_api_key(self, service_name: str) -> Path:
        return (
            self._get_path_service(service_name)
            / "config"
            / "secrets"
            / "api_token.txt"
        )

    def _create_api_key(self, service_name: str):
        """Generates and stores a new API key for the service."""
        api_key = secrets.token_urlsafe(32)
        path_api_key = self._get_path_service_api_key(service_name)
        path_api_key.parent.mkdir(parents=True, exist_ok=True)

        with open(path_api_key, "w") as key_file:
            key_file.write(api_key)

        with open(self.env_file, "a") as env_file:
            env_file.write(f"API_KEY_FOR_{service_name.upper()}={api_key}\n")

    def rotate_api_key(self, service_name: str):
        """Rotates the API key for an existing service."""
        raise NotImplementedError("Method not implemented yet.")
        # This method would follow a similar pattern to _create_api_key,
        # but also update the .env file to replace the old key.
        self.logger.info(f"API key for service '{service_name}' has been rotated.")

    def interactive_menu(self):
        """Presents a menu for service registration or API key rotation."""
        service_options, services = self._list_service_options()
        service_options.append("Exit")
        terminal_menu = TerminalMenu(service_options, title="Select a service or exit:")
        selection_index = terminal_menu.show()

        if selection_index is None or selection_index == len(services):
            self.logger.info("Exiting.")
            return

        selected_service = services[selection_index]
        self.register_service(selected_service)

        # Loop the menu for more actions until exit is chosen
        self.interactive_menu()


# Usage example
if __name__ == "__main__":
    config.setup(__file__, service=False)
    manager = ServiceAPIKeyManager()
    manager.interactive_menu()
