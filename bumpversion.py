import argparse
import subprocess
import warnings
from enum import Enum
from pathlib import Path

import semver

from config import PathRegistry as PR


class SemverParsingError(ValueError):
    pass


class BumpVersionPart(Enum):
    major = "major"
    minor = "minor"
    patch = "patch"
    prerelease = "prerelease"
    build = "build"


def run_command(command):
    """Run a shell command and return the output."""
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"Error executing command: {e.output.decode('utf-8')}") from e


def git_commit_and_tag(service_path: Path, version: semver.Version):
    """Commit the version change and tag the commit."""
    service_name = service_path.name
    # Commit
    commit_message = f"{service_name} v{version}"
    run_command(f"git add {service_path / 'version.py'}")
    run_command(f'git commit -m "{commit_message}"')
    # Tag
    tag_name = f"{service_name}-v{version}"
    run_command(f"git tag -a {tag_name} -m '{commit_message}'")


def get_service_paths() -> dict[str, Path]:
    """Get the paths to all the services."""
    lookup_paths = [PR.PATH_ROOT / "services", PR.PATH_ROOT / "infrastructure"]
    service_paths = {}
    for path in lookup_paths:
        for folder in filter(lambda d: d.is_dir(), path.iterdir()):
            service_paths[folder.name] = folder

    # Adding common code as a service
    service_paths["common"] = PR.PATH_ROOT / "common"

    return service_paths


def read_version(service_path: str | Path) -> semver.Version:
    """Read the version from the service's version.py file."""
    with open(service_path / "version.py", "r") as f:
        version = f.read().strip().split("=")[-1].strip().strip("\"'")

    try:
        return semver.Version.parse(version)
    except ValueError as e:
        raise SemverParsingError(
            f"Error parsing version: {e} in {service_path / 'version.py'}"
        )


def write_version(service_path: str | Path, new_version: semver.Version):
    """Write the new version to the service's version.py file."""
    with open(service_path / "version.py", "w") as f:
        f.write(f'__version__ = "{new_version}"\n')


def bump_version(
    service_path: str | Path, part: BumpVersionPart
) -> tuple[semver.Version, semver.Version]:
    """Bump the version of the service."""
    try:
        old_version = read_version(service_path)
        bump_fun = getattr(old_version, f"bump_{part.value}")
    except FileNotFoundError:
        old_version = semver.Version.parse("0.0.0")
        bump_fun = old_version.bump_minor
        warnings.warn(
            f"Version file not found for service '{service_path.name}', "
            f"creating version 0.1.0 and ignoring part '{part.value}'",
            stacklevel=2,
        )

    new_version = bump_fun()
    write_version(service_path, new_version)
    return old_version, new_version


def main(args: argparse.Namespace):
    service_paths = get_service_paths()

    if args.command == "list":
        for service in service_paths.values():
            print(service.relative_to(PR.PATH_ROOT))

    elif args.command == "bump":
        # Check if the service exists
        try:
            service_path = service_paths[args.service]
        except KeyError:
            raise SystemExit(
                f"Service '{args.service}' not found. Run 'bumpversion.py list' to see all services."
            )

        # Bump the version
        try:
            old_version, new_version = bump_version(
                service_path, BumpVersionPart(args.part)
            )
            print(
                f"Bumped version of service '{args.service}' : {old_version} -> {new_version}"
            )
        except (FileNotFoundError, SemverParsingError) as e:
            raise SystemExit(f"Error bumping version: {e}") from e

        # Commit and tag the version change
        git_commit_and_tag(service_path, new_version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bump the version of a service.")
    subparsers = parser.add_subparsers(
        dest="command", help="Select action", required=True
    )

    # Subcommand to list services
    list_parser = subparsers.add_parser("list", help="List all services")

    # Subcommand to bump version
    bump_parser = subparsers.add_parser(
        "bump",
        help="Bump the version of a service",
        description="Bump the version of a service. The version is read from and written to the service's "
        "version.py file. If the file does not exist, it is created with version 0.1.0.",
    )
    bump_parser.add_argument("service", help="The service to bump the version of")
    bump_parser.add_argument(
        "part",
        choices=[part.value for part in BumpVersionPart],
        help="The part of the version to bump",
    )

    args = parser.parse_args()
    main(args)
