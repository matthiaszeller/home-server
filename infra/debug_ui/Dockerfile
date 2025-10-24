FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py main.py

ENV APP_PORT=8080

CMD ["sh", "-c", "streamlit run main.py --server.port=$APP_PORT --server.address=0.0.0.0 --server.runOnSave true"]
