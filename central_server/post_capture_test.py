import requests


url = "https://netsparrow.viktorkirk.com/packet_capture/"

data = {
    "ip": "130.225.37.168",
    "url": "None"
}

headers = {
    "Authorization": "Token f990deebf6b6f888560a4b2bc131989496a55030",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=data) 

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
