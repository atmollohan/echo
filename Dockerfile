# Echo Lab Protocol Generator Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY requirements.txt ./
COPY app.py ./
COPY config.example.ini ./
COPY echo_run/ ./echo_run/
COPY notebooks/ ./notebooks/
COPY data/ ./data/

# Install the project and its dependencies.
RUN pip install --no-cache-dir .

# Expose Streamlit port
EXPOSE 8501

# Set environment for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV ECHO_NOTEBOOKS_DIR=/app/notebooks
ENV ECHO_DATA_DIR=/app/data

# Run the installed console script
CMD ["echo-run"]
