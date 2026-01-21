FROM python:3.12-slim
WORKDIR /app
COPY server.py /app/server.py
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "server.py"]
    