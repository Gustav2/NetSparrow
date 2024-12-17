import requests

# API endpoint
url = "https://netsparrow.viktorkirk.com/api/settings/get/pi/"

# User token for authentication
headers = {
    "Authorization": "Token f990deebf6b6f888560a4b2bc131989496a55030",
}

# Make the GET request
response = requests.get(url, headers=headers)

# Print the response
print(response.status_code)
print(response.json())
