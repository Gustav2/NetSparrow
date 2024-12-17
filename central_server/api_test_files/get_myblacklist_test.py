import requests

# API endpoint
url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"

# User token for authentication
headers = {
    "Authorization": "Token f990deebf6b6f888560a4b2bc131989496a55030",
    "Content-Type": "application/json"
}

# Make the GET request
response = requests.get(url, headers=headers)

# Print the response
print("Status Code:", response.status_code)
print("Response JSON:", response.json())