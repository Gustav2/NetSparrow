import requests

# The API endpoint
url = "https://netsparrow.viktorkirk.com/packet_capture/"

# Data to be sent
data = {
    "ip" : "2.1.1.1",
    "url" : "https://www.youtube.com",
    "user_id" : 1,
}

# A POST request to the API
for i in range (20):
    response = requests.post(url, json=data)

    # Print the response
    print(response.json())
