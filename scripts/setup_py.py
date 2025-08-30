import argparse
import logging

import git

from ops.bootstrap.conda import ensure_conda
from ops.bootstrap.repo import ensure_repo
from ops.bootstrap.ssh import SSH

REMOTE_PORT = 8443
REMOTE_DEST = "/opt/home-server"
REMOTE_CONDA_ENV = "home-server-ctrl"

logger = logging.getLogger(__name__)


def init_ssh(*args, **kwargs) -> SSH:
    ssh = SSH(*args, **kwargs)
    if not ssh.ping():
        raise RuntimeError("Cannot connect to remote host")

    logger.info(f"SSH connection established to {args} {kwargs}")
    return ssh


def get_repo_url() -> str:
    repo = git.Repo(search_parent_directories=True)
    url = repo.remote().url

    return url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host", help="Hostname, e.g. defined in SSH config")
    ap.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    # if verbose, show paramiko:INFO. if not, hide it
    logging.getLogger("paramiko").setLevel(
        logging.INFO if args.verbose else logging.WARNING
    )
    # if verbose, show invoke:INFO. if not, hide it
    logging.getLogger("invoke").setLevel(
        logging.INFO if args.verbose else logging.WARNING
    )

    # 0) Initialize SSH connection
    ssh = init_ssh(args.host)

    # 1) Conda
    ensure_conda(ssh, REMOTE_CONDA_ENV, python_version="3.13")

    # 2) Repo
    repo_url = get_repo_url()
    ensure_repo(ssh, repo_url, REMOTE_DEST)


if __name__ == "__main__":
    main()
