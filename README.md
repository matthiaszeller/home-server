# Home Server


## Development

### Getting Started

Install pre-commit
```shell
pip install pre-commit
```

Initialize
```shell
pre-commit install
```

### Adding Services

Create a new directory `services/myservice`, containing:

- `main.py` file:
```python
from common.config import setup
setup(__file__)
# other imports
from time import sleep

if __name__ == '__main__':
    sleep(1)
```
- `src/` directory with all service-specific code
- `config/` directory with service-specific config files (create even if empty)
- `requirements.txt`
- `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY ./services/<myservice> .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./common ./common
COPY ./config/* ./config


ENTRYPOINT ["tail", "-f", "/dev/null"]
```

And add in the `docker-compose.yaml`:
```yaml
  myservice:
    build:
      dockerfile: services/<myservice>/Dockerfile
    depends_on:
      - ...
    networks:
      - app_net
```

### Test Locally

For quick testing and debugging purposes, run services as python package, e.g.,
```bash
python -m services.tgbot.main
```
