import logging

from .ssh import SSH

logger = logging.getLogger(__name__)


def ensure_repo(ssh: SSH, repo_url: str, dest_path: str, branch: str = "main"):
    # check if git repo
    res = ssh.sh(f"git -C {dest_path} rev-parse --is-inside-work-tree", pty=True)
    if not res.ok:
        # not a git repo, clone it
        logger.info(f"cloning repo {repo_url} to {dest_path}")
        res = ssh.sh(
            f"git clone {repo_url} {dest_path}",
            sudo=True,
            pty=False,
            timeout=30,
            env={"GIT_SSH_COMMAND": "ssh -o StrictHostKeyChecking=accept-new"},
        )
        if not res.ok:
            err = res.stderr.strip() or res.stdout.strip()
            raise RuntimeError(f"failed to clone repo: {err}")

    # fetch latest
    logger.info(f"updating repo at {dest_path}")
    res = ssh.sh(
        f"git -C {dest_path} fetch --all -p && git -C {dest_path} reset origin/{branch}",
        pty=True,
    )
    if not res.ok:
        raise RuntimeError(f"failed to update repo: {res.stderr.strip()}")
