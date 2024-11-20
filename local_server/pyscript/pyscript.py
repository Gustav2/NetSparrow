import requests
from pathlib import Path
from fastapi import FastAPI, status
from pydantic import BaseModel
import uvicorn
import time

centralToken = "Token f990deebf6b6f888560a4b2bc131989496a55030"

tempSettings = {
    "mlPercentage": 100,
    "caution": 5
}

app = FastAPI()
blacklist_path = Path('/shared/blacklist.txt')

class Data(BaseModel):
    value: str

class Settings(BaseModel):
    mlPercentage: int
    caution: int

@app.post("/settings", status_code=status.HTTP_200_OK)
def handle_settings(data: Settings):
    print("Settings received")
    print("mlPercentage: " + str(data.mlPercentage))
    print("Caution: " + str(data.caution))
    return {"status": "success"}

    # % of packages to ML
    #

@app.get("/settings")
def get_settings():
    return {"mlPercentage": tempSettings["mlPercentage"], "caution": tempSettings["caution"]}

@app.get("/test")
def test():
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

    with open(blacklist_path, 'w', newline='') as file:
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

    with open(blacklist_path, 'r') as file:
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
    while True:
        print("pulling")
        pullBlacklist(centralToken)
        print("pulled blacklist")
        time.sleep(5)
        print("sleep")
    #pushBlacklist(centralToken)
    #uvicorn.run(app, host="0.0.0.0", port=8000)
