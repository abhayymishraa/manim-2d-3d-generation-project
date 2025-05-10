FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install only necessary system packages for Manim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2-dev \
    libpango1.0-dev \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-science \
    tipa \
    libffi-dev \
    git \
    build-essential \
    pkg-config \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create render directory with open permissions
RUN mkdir -p /app/renders && chmod 777 /app/renders

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
