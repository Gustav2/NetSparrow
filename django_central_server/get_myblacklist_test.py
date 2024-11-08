import requests

url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"

headers = {
    "Authorization": "Token ec189526a1ff4dcf88b10b269522b4718538d9f7",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())