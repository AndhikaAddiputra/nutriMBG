FROM python:3.9-slim AS builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.9-slim

RUN groupadd -r nutrimbg && useradd -r -g nutrimbg nutrimbg

WORKDIR /app
COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/app/ app/
COPY backend/scripts/ scripts/
COPY backend/artifacts/ artifacts/
COPY dataset/ dataset/

EXPOSE 8000

USER nutrimbg

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
