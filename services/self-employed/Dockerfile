
FROM python:3.10-slim

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock* /app/

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-cache

#
COPY run_invoice.py .

CMD ["poetry", "run", "streamlit", "run", "run_invoice.py", "--server.port", "5000", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false", "--server.headless", "true", "--logger.level=debug"]
