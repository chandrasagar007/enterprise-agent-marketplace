# Use a lightweight Python base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system-level dependencies required for building C-extensions (like ChromaDB)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 🚀 ADD THIS EXACT LINE: Create the empty logs folder
RUN mkdir -p logs

# Copy the rest of the enterprise codebase into the container
COPY . .

# Explicitly set the python path so modules can find each other
ENV PYTHONPATH=/app