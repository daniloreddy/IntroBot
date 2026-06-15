FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY introbot.py .
COPY cogs/ ./cogs/
COPY services/ ./services/
COPY utils/ ./utils/

CMD ["python", "introbot.py"]
