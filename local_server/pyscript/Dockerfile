# pull official base image
FROM python:3.12-alpine

# set work directory
WORKDIR /pyscript

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY pyscript.py .

# Command to run the script
CMD ["python3", "pyscript.py"]