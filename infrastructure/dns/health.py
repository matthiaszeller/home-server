import json
import sys
from pathlib import Path


def check_logs(file: Path) -> bool:
    res = json.loads(file.read_text())

    return res.get("success", False) is True


def main():
    path = Path(__file__).parent.joinpath("logs")
    files = path.glob("state_*.json")

    for f in files:
        if not check_logs(f):
            print(f"DNS health check failed: {f}")
            sys.exit(1)
