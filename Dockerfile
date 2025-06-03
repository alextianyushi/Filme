FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN pip install uv

# Copy project files
COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/prompts/ ./prompts/
COPY backend/main.py ./

# Install Python dependencies
RUN uv sync --frozen

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Start application
CMD uv run uvicorn main:app --host 0.0.0.0 --port $PORT 