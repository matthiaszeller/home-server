from pathlib import Path


def read_text_file(path: str | Path):
    with open(path, "r") as fh:
        return fh.read().strip()
