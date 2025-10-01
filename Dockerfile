FROM python:3.10.13-slim-bullseye



# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirement.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the app
COPY . .

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.headless=true"]
