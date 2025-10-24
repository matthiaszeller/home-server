import sys
from pathlib import Path

from providers import DNSUpdateResult


def check_logs(file: Path) -> bool:
    res = DNSUpdateResult.model_validate_json(file.read_text())

    return res.is_successful


def main():
    path = Path(__file__).parent.joinpath("logs")
    files = path.glob("state_*.json")

    for f in files:
        if not check_logs(f):
            print(f"DNS health check failed: {f}")
            sys.exit(1)


if __name__ == "__main__":
    main()
