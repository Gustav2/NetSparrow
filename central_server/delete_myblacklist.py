import requests
import json

url = "https://netsparrow.viktorkirk.com/settings/remove_from_myblacklist/"
headers = {
    "Authorization": "Token 71c08c598319cded9587ff36b0069226fd0565a1",
    "Content-Type": "application/json"
}
data = {
    "ip": "1.1.1.1",
    "url": "Https://www.google.com"
}

response = requests.delete(url, headers=headers, data=json.dumps(data))

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
