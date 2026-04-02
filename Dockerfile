# Echo Lab Protocol Generator Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY requirements.txt .  # Fallback
COPY app.py .
COPY config.example.ini .
COPY notebooks/ ./notebooks/
COPY data/ ./data/

# Install Python dependencies
# Try uv first (faster), fall back to pip
RUN pip install uv 2>/dev/null && \
    uv pip install --system -r pyproject.toml 2>/dev/null || \
    pip install -r pyproject.toml || \
    pip install streamlit pandas numpy matplotlib tqdm papermill jupyter

# Expose Streamlit port
EXPOSE 8501

# Set environment for Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]