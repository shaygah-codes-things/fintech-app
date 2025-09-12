FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn httpx
COPY ./app ./app
# ensure package
RUN [ -f app/__init__.py ] || touch app/__init__.py
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
