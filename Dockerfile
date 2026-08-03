FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY validator ./validator
COPY domains ./domains
COPY api ./api
COPY pytest.ini .

ENV ONTOHARNESS_DOMAINS_DIR=/app/domains

EXPOSE 8010

CMD ["python", "-m", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8010"]
