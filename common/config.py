import json
import logging.config
import os
import sys
from pathlib import Path
from typing import Iterable, Any

import yaml


class ServiceRegistry:

    SERVICE_TGBOT_PORT = 5000

    @classmethod
    def get_service_hostname(cls, service: str) -> str:
        local = os.environ.get('LOCAL_SERVICE_NAME') is not None
        if local:
            return 'localhost'
        return service


class PathRegistry:
    """Utility class for managing and accessing filesystem paths within the project."""
    PATH_ROOT = Path()
    PATH_CONFIG = 'config'
    PATH_LOGS = 'logs'

    @classmethod
    def setup(cls, path_call_file: str):
        cls.PATH_ROOT = Path(path_call_file).parent.absolute()
        if cls.PATH_ROOT.parent.name == 'services':
            os.environ['LOCAL_SERVICE_NAME'] = cls.PATH_ROOT.name

        for path in dir(PathRegistry):
            if path.startswith('PATH_'):
                # rewrite paths
                setattr(cls, path, cls.PATH_ROOT / getattr(cls, path))

        cls.PATH_LOGS.mkdir(exist_ok=True)

    @classmethod
    def get_config_file(cls, fname: str) -> Path:
        service_config = cls.PATH_CONFIG / fname
        if os.environ.get('LOCAL_SERVICE_NAME') is not None:
            local_config = cls.PATH_ROOT.parent.parent / 'config' / fname
            if local_config.exists():
                return local_config

        return service_config

    @classmethod
    def glob_config(cls, glob: str) -> list[Path]:
        files = list(cls.PATH_CONFIG.glob(glob))
        if os.environ.get('LOCAL_SERVICE_NAME') is not None:
            files.extend(cls.PATH_ROOT.parent.parent.joinpath('config').glob(glob))

        return files


def setup_logging():
    def merge_logging_configs(paths: Iterable[Path], allow_overwrite: bool = False) -> dict[str, Any]:
        merged_config = dict()
        for file in paths:
            with file.open('r') as fh:
                cfg = yaml.safe_load(fh.read())

            for k, v in cfg.items():
                if k in merged_config:
                    if k == 'version':
                        assert merged_config[k] == v, 'found mismatching logging config versions in config/config_*.yaml'
                        continue

                    if not allow_overwrite:
                        intersect = set(v.keys()).intersection(merged_config[k].keys())
                        assert len(intersect) == 0,  f'overlapping fields in logging config: {", ".join(intersect)}'

                    merged_config[k].update(v)
                else:
                    merged_config[k] = v

        return merged_config

    files_config_logs = PathRegistry.glob_config('logging_*.yaml')
    cfg = merge_logging_configs(files_config_logs)
    # file paths
    for handler_dic in cfg['handlers'].values():
        if 'filename' in handler_dic:
            handler_dic['filename'] = str(PathRegistry.PATH_LOGS / Path(handler_dic['filename']).name)

    logging.config.dictConfig(cfg)


def setup(call_file):
    PathRegistry.setup(call_file)
    setup_logging()

    # setup python path for local testing
    if os.environ.get('LOCAL_SERVICE_NAME') is not None:
        sys.path.insert(0, str(PathRegistry.PATH_ROOT))
