FROM python:3.12.9-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# No longer need to copy. Mount them instead
# COPY src/ .

# Command to run the Discord bot
CMD ["python", "discord_app.py"]