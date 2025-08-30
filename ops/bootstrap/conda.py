import logging

from .ssh import SSH

logger = logging.getLogger(__name__)


def ensure_conda(ssh: SSH, env_name: str, python_version: str = "3.13"):
    # check conda installed and visible
    conda = ssh.get_conda_path()
    if not conda:
        raise RuntimeError("Conda not found on remote host")

    # gather info
    conda_info = ssh.get_output_json(f"{conda} info --json")
    logger.info(
        f"found conda version {conda_info.get('conda_version', '<unknown>')} at {conda}"
    )

    # create env if needed
    env_py_version = ssh.sh(f"{conda} run -n {env_name} python --version", pty=True)
    if not env_py_version.ok:
        logger.info(f"creating conda env '{env_name}'")
        res = ssh.sh(
            f"{conda} create -n {env_name} python={python_version} -y",
            pty=True,
            timeout=300,
        )
        if not res.ok:
            raise RuntimeError(f"failed to create conda env: {res.stderr.strip()}")

        # rerun
        env_py_version = ssh.sh(f"{conda} run -n {env_name} python --version", pty=True)
        if not env_py_version.ok:
            raise RuntimeError(
                f"failed to verify conda env after creation: {env_py_version.stderr.strip()}"
            )

    env_py_version = env_py_version.stdout.strip()
    logger.info(f'found conda env "{env_name}" with python version {env_py_version}')
