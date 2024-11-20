import requests
import json

# The data needs to be formatted as a dictionary matching the Data model
data = {
    "value": "your string here"
}

# Send POST request with JSON data
response = requests.post("http://localhost:8000/endpoint", json=data)
print(response.json())
