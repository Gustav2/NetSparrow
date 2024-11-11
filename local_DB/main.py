import requests

# The API endpoint
url = "https://netsparrow.viktorkirk.com/settings/myblacklist/?user_id=2"


# Data to be sent
data = {
    "user_id" : 2,
}

# A POST request to the API
response = requests.get(url, json=data)

# Print the response
print(response.json())
