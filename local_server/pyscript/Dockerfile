# pull official base image
FROM python:3.12-alpine

# set work directory
WORKDIR /pyscript

# Copy the Python script into the container
COPY . /pyscript

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the script
CMD ["python3", "pyscript.py"]