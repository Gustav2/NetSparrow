# pull official base image
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# set work directory
WORKDIR /ml

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY always_cli.py .
COPY best_packet_classifier.keras .

# Command to run the script
CMD ["python3", "always_cli.py", "best_packet_classifier.keras"]