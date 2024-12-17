import requests

# API endpoint
url = "https://netsparrow.viktorkirk.com/packet_capture/"

data = {
    "ip": "024.034.224",
    "url": "None"
}

# User token for authentication
headers = {
    "Authorization": "Token f990deebf6b6f888560a4b2bc131989496a55030",
    "Content-Type": "application/json"
}

# Make the POST request
response = requests.post(url, headers=headers, json=data) 

# Print the response
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
