FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies (needed for psycopg2 and other compilation if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY ./backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Command to run (overridden in docker-compose for dev)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
