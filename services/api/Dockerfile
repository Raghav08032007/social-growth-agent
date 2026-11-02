FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-lock.txt ./
RUN pip install --no-cache-dir -c requirements-lock.txt -r requirements.txt
RUN useradd --create-home appuser
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 5000
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "--call", "growth:create_app"]
