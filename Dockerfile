FROM python:3.11-slim

LABEL maintainer="Anti-Slop Kit Contributors"
LABEL description="Anti-Slop Kit - AI code quality linter"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . .

# Set the entrypoint
ENTRYPOINT ["aslint"]
CMD ["--help"]
