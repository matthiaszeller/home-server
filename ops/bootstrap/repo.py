import logging

from .ssh import SSH

logger = logging.getLogger(__name__)


def ensure_repo(ssh: SSH, repo_url: str, dest_path: str, branch: str = "main"):
    # check if git repo
    res = ssh.sh(f"git -C {dest_path} rev-parse --is-inside-work-tree", pty=True)
    if not res.ok:
        # create parent dir with sudo then chown to user
        logging.info(f"ensuring parent dir for {dest_path}")
        ssh.sh(
            f"sudo mkdir -p {dest_path} && sudo chown $(whoami) {dest_path}",
            pty=False,
            sudo=True,
        )

        # not a git repo, clone it
        logger.info(f"cloning repo {repo_url} to {dest_path}")
        # refuse new host keys, user has to set it up
        res = ssh.sh(
            f'git -c core.sshCommand="ssh -o StrictHostKeyChecking=yes" '
            f"clone --depth 1 {repo_url} {dest_path}",
            pty=False,
            timeout=30,
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
