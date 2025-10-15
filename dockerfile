FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create temp directories with proper permissions
RUN mkdir -p /tmp/github_analytics/plots && \
    mkdir -p /tmp/github_analytics/csv && \
    chmod -R 755 /tmp/github_analytics

WORKDIR /app
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PORT 8080
EXPOSE 8080

CMD ["python", "app.py"]