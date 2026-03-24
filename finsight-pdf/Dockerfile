FROM python:3.11-slim

# Install system libraries needed by pdfplumber and pikepdf
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    poppler-utils \
    libqpdf-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY main.py .

# Hugging Face Spaces runs on port 7860
EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]