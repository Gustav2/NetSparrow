import requests
# test for delete myblacklist url or ip in myblacklist
url = "https://netsparrow.viktorkirk.com/remove_from_myblacklist/"
"""
headers = { "Authorization": "Token 71c08c598319cded9587ff36b0069226fd0565a1", "Content-Type": "application/json" }

 {'blacklist_entry__capturedpacket_entry__ip': '10.10.10.10', 'blacklist_entry__capturedpacket_entry__url': None}

response = requests.post(url, headers=headers, json={"blacklist_id": 1})

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
"""


