import requests
import json

# API endpoint
url = "https://netsparrow.viktorkirk.com/settings/remove_from_myblacklist/"

# User token for authentication
headers = {
    "Authorization": "Token 71c08c598319cded9587ff36b0069226fd0565a1",
    "Content-Type": "application/json"
}
data = {
    "ip": "1.1.1.1",
    "url": "Https://www.google.com"
}

# Make the DELETE request
response = requests.delete(url, headers=headers, data=json.dumps(data))

# Print the response
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
