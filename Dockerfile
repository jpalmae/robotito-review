FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project to /app
COPY . .

EXPOSE 8000 8501

# Usamos CMD en lugar de ENTRYPOINT para que docker-compose pueda sobrescribirlo fácilmente para la API
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
