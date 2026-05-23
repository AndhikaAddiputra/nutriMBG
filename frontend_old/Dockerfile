FROM python:3.9-slim

RUN groupadd -r nutrimbg && useradd -r -g nutrimbg nutrimbg

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=nutrimbg:nutrimbg . .

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8501

USER nutrimbg

CMD ["streamlit", "run", "00_Beranda.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
