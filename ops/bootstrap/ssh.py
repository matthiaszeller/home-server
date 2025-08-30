import json
import logging
from contextlib import contextmanager
from getpass import getpass
from typing import Any

from fabric import Config, Connection, Result


class SSH:

    def __init__(self, *args, **kwargs):
        """
        Initialize the SSH connection, args and kargs are passed to fabric.Connection
        """
        self.args = args
        self.kwargs = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)
        self._conda = None
        self.__password = None

    @contextmanager
    def con(self, **kwargs):
        with Connection(*self.args, **self.kwargs, **kwargs) as c:
            yield c

    @property
    def _password(self) -> str:
        if self.__password is None:
            self.__password = getpass("Remote sudo password:")

        return self.__password

    def get_conda_path(self) -> str | None:
        if self._conda is None:
            res = self.sh("bash -lc 'command -v conda || true'", pty=True)
            if res.ok:
                path = res.stdout.strip()
                if path:
                    self._conda = path

        return self._conda

    def ping(self):
        res = self.sh("echo pong", pty=False)
        return res.ok and res.stdout.strip() == "pong"

    def sh(
        self,
        command: str,
        *,
        sudo: bool = False,
        pty: bool = True,
        timeout: float = 10.0,
        warn: bool = True,
        **kwargs,
    ) -> Result:
        config = None
        if sudo:
            config = Config(
                overrides={
                    "sudo": {
                        "password": self._password,
                    }
                }
            )

        with self.con(config=config) as c:
            self.logger.debug(
                f"running command: {command} (pty={pty}, kwargs={kwargs})"
            )
            cmd_fun = c.sudo if sudo else c.run
            res = cmd_fun(
                command, hide=True, pty=pty, warn=warn, timeout=timeout, **kwargs
            )
            return res

    def get_output(self, command: str, **kwargs) -> str:
        res = self.sh(command, **kwargs)
        if res.ok:
            return res.stdout.strip()

        raise RuntimeError(
            f"command failed: {command} (exit code {res.exited}), stderr: {res.stderr.strip()}"
        )

    def get_output_json(self, command: str, **kwargs) -> Any:
        output = self.get_output(command, **kwargs)
        return json.loads(output)

    def put(self, local: str, remote: str):
        with self.con() as c:
            self.logger.debug(f"putting file: {local} to {remote}")
            c.put(local, remote)

    def get(self, remote: str, local: str):
        with self.con() as c:
            self.logger.debug(f"getting file: {remote} to {local}")
            c.get(remote, local)
