import argparse
import logging
import zipfile
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import git

from ops.bootstrap.conda import ensure_conda
from ops.bootstrap.repo import ensure_repo
from ops.bootstrap.ssh import SSH

REMOTE_PORT = 8443
PATH_ROOT = Path(__file__).absolute().parent.parent
REMOTE_DEST = "/opt/home-server"
REMOTE_CONDA_ENV = "home-server-ctrl"

logger = logging.getLogger(__name__)


@contextmanager
def init_ssh(*args, **kwargs):
    ssh = SSH(*args, **kwargs)

    with ssh:
        if not ssh.ping():
            raise RuntimeError("Cannot connect to remote host")

        logger.info(f"SSH connection established to {args} {kwargs}")

        yield ssh


def get_repo_url() -> str:
    repo = git.Repo(search_parent_directories=True)
    url = repo.remote().url

    return url


@contextmanager
def temp_zip(folder: Path):
    with NamedTemporaryFile(suffix=".zip", prefix="home-server-") as tmpf:
        # create zip of folder
        with zipfile.ZipFile(tmpf.name, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in folder.rglob("*"):
                zf.write(file, file.relative_to(folder))

        yield tmpf.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("host", help="Hostname, e.g. defined in SSH config")
    ap.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    ap.add_argument(
        "-b", "--branch", default="main", help="Git branch to checkout on remote"
    )

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
    with init_ssh(args.host) as ssh:

        # 1) Conda
        ensure_conda(ssh, REMOTE_CONDA_ENV, python_version="3.13")

        # 2) Repo
        repo_url = get_repo_url()
        ensure_repo(ssh, repo_url, REMOTE_DEST, branch=args.branch)

        # 3) Copy sudo scripts
        path_sudo_scripts = Path("ops", "scripts", "sudo")
        with temp_zip(PATH_ROOT / path_sudo_scripts) as zip_path:
            logging.info(f"Uploading sudo scripts from {path_sudo_scripts}...")
            ssh.put(
                local=zip_path,
                remote=str("/tmp/home-server-scripts.zip"),
            )
        # unzip and run install.sh with sudo
        logging.info("Installing sudo scripts...")
        res = ssh.sh(
            "unzip -o /tmp/home-server-scripts.zip -d /tmp/home-server-scripts && "
            "sudo bash /tmp/home-server-scripts/install.sh && "
            "rm -rf /tmp/home-server-scripts /tmp/home-server-scripts.zip",
            pty=False,
            sudo=True,
        )
        if not res.ok:
            raise RuntimeError(f"failed to install sudo scripts: {res.stderr.strip()}")

        # ...

        # X) Start server (idempotent; kill old if running)


if __name__ == "__main__":
    main()
