# Use Python 3.10 slim
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose HuggingFace default port
EXPOSE 7860

# Start Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
