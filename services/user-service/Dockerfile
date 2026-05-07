# Use the official lightweight Python 3.11 image as our base
# "slim" means it's a smaller version — fewer built-in tools, faster to download
FROM python:3.11-slim

# Set the working directory inside the container
# All subsequent commands will run from this folder
WORKDIR /app

# Copy requirements.txt first (before the rest of the code)
# Docker caches this layer — so if requirements don't change,
# it won't reinstall packages every time we rebuild
COPY requirements.txt .

# Install all Python dependencies listed in requirements.txt
# --no-cache-dir means don't store the download cache — keeps image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our service code into the container
COPY . .

# Tell Docker this container listens on port 8001
# This is documentation only — the actual port mapping is in docker-compose.yml
EXPOSE 8001

# The command that runs when the container starts
# uvicorn = our web server, main:app = file:variable, 
# --host 0.0.0.0 means accept connections from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]