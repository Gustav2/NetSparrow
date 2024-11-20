import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

centralToken = "Token 71c08c598319cded9587ff36b0069226fd0565a1"

app = FastAPI()

class Data(BaseModel):
    value: str

@app.post("/endpoint")
async def handle_request(data: Data):
    # Process your data here
    print("Data received")
    print(data.value)
    return {"status": "success"}

@app.post("/settings")
def handle_settings(data: Data):
    print("Settings received")
    print(data.value)
    return {"status": "success"}

def pullBlacklist(token):
    url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    print(response.json())
    blacklist_data = response.json()["myblacklists"]

    with open('ip_addresses', 'w', newline='') as file:
        for i in blacklist_data:
            ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
            file.write(ip + "\n")
            #url = str(i["blacklist_entry__capturedpacket_entry__url"])

def pushBlacklist(token):
    url = "https://netsparrow.viktorkirk.com/packet_capture/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    with open('ip_addresses', 'r') as file:
        for line in file:
            data = {
                "ip": line.strip()
            }
            print(data)

            response = requests.post(url, headers=headers, json=data)
            print(url, headers, data)
            print("Status Code:", response.status_code)
            print("Response JSON:", response.json())


if __name__ == "__main__":
    pullBlacklist(centralToken)
    #pushBlacklist(centralToken)
    uvicorn.run(app, host="0.0.0.0", port=8000)
