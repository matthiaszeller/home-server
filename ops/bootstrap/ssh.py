import json
import logging
import socket
import time
from getpass import getpass
from typing import Any, Optional

from fabric import Connection, Result
from invoke.exceptions import UnexpectedExit
from paramiko.ssh_exception import SSHException


class SSH:
    def __init__(
        self,
        *args,
        keepalive: int = 30,
        max_retries: int = 2,
        retry_delay: float = 0.5,
        **kwargs,
    ):
        """
        Args/kwargs → fabric.Connection. Keeps a single connection open and reused.
        """
        self.args = args
        self.kwargs = kwargs
        self.keepalive = keepalive
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.logger = logging.getLogger(self.__class__.__name__)
        self._conda: Optional[str] = None
        self.__password: Optional[str] = None
        self._c: Optional[Connection] = None

    # --- connection lifecycle ---

    def open(self) -> Connection:
        if self._c is None:
            # If caller provided a Config in kwargs, keep it; else create default.
            self._c = Connection(*self.args, **self.kwargs)
        if not getattr(self._c, "is_connected", False):
            self._c.open()
            try:
                t = self._c.transport
                if t is not None and self.keepalive:
                    t.set_keepalive(self.keepalive)
            except Exception as e:
                self.logger.debug(f"keepalive setup failed (non-fatal): {e}")
        return self._c

    def close(self):
        if self._c is not None:
            try:
                self._c.close()
            finally:
                self._c = None

    def __enter__(self) -> "SSH":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # --- sudo password (cached) ---

    @property
    def _password(self) -> str:
        if self.__password is None:
            self.__password = getpass("Remote sudo password:")
        return self.__password

    # --- internal retry wrapper ---

    def _retry(self, fn, *args, **kwargs):
        attempts = 0
        while True:
            attempts += 1
            try:
                return fn(*args, **kwargs)
            # transport-level failures: reconnect and retry
            except (SSHException, EOFError, socket.error) as e:
                if attempts > self.max_retries:
                    raise
                self.logger.warning(
                    f"SSH transport error ({e}); reconnecting… "
                    f"{attempts}/{self.max_retries}"
                )
                self.close()
                time.sleep(self.retry_delay)
                self.open()
            # command non-zero → propagate
            except UnexpectedExit:
                raise

    # --- public API ---

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
        c = self.open()

        # Per-call sudo config override without rebuilding the connection:
        # Fabric reads sudo.password from c.config; we can clone a transient view.
        if sudo:
            # Merge a lightweight override just for this call.
            # Config has .overrides but easiest is to build a derived Config and use c.sudo(password=...)
            # However Fabric's sudo() does not accept password kw; it reads from config.
            # So temporarily set, run, then restore.
            old_pwd = c.config.sudo.password if hasattr(c.config, "sudo") else None
            # Ensure nested keys exist
            c.config.load_overrides({"sudo": {"password": self._password}})
            try:
                self.logger.debug(f"sudo: {command}")
                return self._retry(
                    c.sudo,
                    command,
                    hide=True,
                    pty=pty,
                    warn=warn,
                    timeout=timeout,
                    **kwargs,
                )
            finally:
                # restore prior value (or remove if it was None)
                if old_pwd is None:
                    c.config.load_overrides({"sudo": {"password": None}})
                else:
                    c.config.load_overrides({"sudo": {"password": old_pwd}})
        else:
            self.logger.debug(f"run: {command}")
            return self._retry(
                c.run, command, hide=True, pty=pty, warn=warn, timeout=timeout, **kwargs
            )

    def get_output(self, command: str, **kwargs) -> str:
        res = self.sh(command, **kwargs)
        if res.ok:
            return res.stdout.strip()
        raise RuntimeError(
            f"command failed: {command} (exit code {res.exited}), stderr: {res.stderr.strip()}"
        )

    def get_output_json(self, command: str, **kwargs) -> Any:
        return json.loads(self.get_output(command, **kwargs))

    def get_conda_path(self) -> Optional[str]:
        if self._conda is None:
            res = self.sh("bash -lc 'command -v conda || true'", pty=False)
            if res.ok:
                path = res.stdout.strip()
                if path:
                    self._conda = path
        return self._conda

    def ping(self) -> bool:
        res = self.sh("echo pong", pty=False)
        return res.ok and res.stdout.strip() == "pong"

    def put(self, local: str, remote: str):
        c = self.open()
        self.logger.debug(f"put {local} → {remote}")
        return self._retry(c.put, local, remote)

    def get(self, remote: str, local: str):
        c = self.open()
        self.logger.debug(f"get {remote} → {local}")
        return self._retry(c.get, remote, local)
