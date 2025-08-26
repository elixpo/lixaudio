# Base image with CUDA runtime for GPU
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install Python 3.12 from deadsnakes PPA + build tools + ffmpeg
RUN apt-get update && apt-get install -y software-properties-common wget \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
       python3.12 python3.12-venv python3.12-distutils python3-pip \
       build-essential ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy requirements and install
COPY requirements.txt .
RUN python3.12 -m pip install --upgrade pip --no-cache-dir
RUN python3.12 -m pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Set Flask app entry point
ENV FLASK_APP=src/app.py
CMD ["python3.12", "src/app.py"]
