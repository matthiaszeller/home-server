import logging.config
from pathlib import Path
from typing import Any, Iterable

import yaml


class PathRegistry:
    """Utility class for managing and accessing filesystem paths within the project."""

    PATH_ROOT = Path(__file__).parent.absolute()
    PATH_CONFIG = PATH_ROOT / "config"
    PATH_LOGS = PATH_ROOT / "logs"


# create folders if needed
for path in dir(PathRegistry):
    if path.startswith("PATH_"):
        getattr(PathRegistry, path).mkdir(exist_ok=True)


def setup_logging():
    def merge_logging_configs(
        paths: Iterable[Path], allow_overwrite: bool = False
    ) -> dict[str, Any]:
        merged_config = dict()
        for file in paths:
            with file.open("r") as fh:
                cfg = yaml.safe_load(fh.read())

            for k, v in cfg.items():
                if k in merged_config:
                    if k == "version":
                        assert (
                            merged_config[k] == v
                        ), "found mismatching logging config versions in config/config_*.yaml"
                        continue

                    if not allow_overwrite:
                        intersect = set(v.keys()).intersection(merged_config[k].keys())
                        assert (
                            len(intersect) == 0
                        ), f'overlapping fields in logging config: {", ".join(intersect)}'

                    merged_config[k].update(v)
                else:
                    merged_config[k] = v

        return merged_config

    files_config_logs = PathRegistry.PATH_CONFIG.glob("logging_*.yaml")
    cfg = merge_logging_configs(files_config_logs)
    logging.config.dictConfig(cfg)
