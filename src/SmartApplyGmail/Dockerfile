FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup --no-create-home appuser

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
    
# NOSONAR - .dockerignore excludes all sensitive files   
COPY . . 

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8004

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
