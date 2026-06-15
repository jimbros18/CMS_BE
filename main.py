import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import NewClient
from crud import addNewClient, deleteClient, getClient, getClients, getCoffins, updateClient, getPlans, getAllLights

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["*"] for all (dev only)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/+client")
async def add_client(newClient: NewClient):
    data = addNewClient(newClient)
    print("New client added with ID:", data)
    return {
        "success": True,
        "message": "Client added successfully",
        "client_id": data
    }

@app.get("/*clients")
def get_clients():
    clients = getClients()
    return clients

@app.delete("/-client/{client_id}")
def delete_client(client_id: int):
    deleteClient(client_id)
    return f"{client_id} deleted successfully"

@app.get("/getclient/{client_id}")
def get_client(client_id: int):
    client = getClient(client_id)
    return client

@app.put("/~client/{client_id}")
def update_client(client_id: int, payload: dict):
    updated_data = updateClient(client_id, payload)
    # print('updated: ', payload)
    return updated_data

@app.get("/coffins")
def coffins():
    return getCoffins()

@app.get("/plans")
def plans():
    return getPlans()

@app.get("/lights")
def lights():
    return getAllLights()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)