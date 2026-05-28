# Actualizamos a la versión 1.60.0
FROM mcr.microsoft.com/playwright/python:v1.60.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY centinela.py .
EXPOSE 5000
CMD ["python", "-u", "centinela.py"]
