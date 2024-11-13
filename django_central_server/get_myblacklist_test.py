import requests

url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"

headers = {
    "Authorization": "Token 71c08c598319cded9587ff36b0069226fd0565a1",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())