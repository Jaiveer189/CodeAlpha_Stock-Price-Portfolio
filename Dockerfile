# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (better caching — only reinstalls if requirements change)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# HF Spaces requires port 7860 — must match what Flask runs on
EXPOSE 7860

# Start the Flask app
CMD ["python", "app.py"]