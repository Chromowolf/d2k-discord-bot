FROM python:3.12.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python source files from src/ to app's root
COPY src/ .

# Command to run the Discord bot
CMD ["python", "discord_app.py"]