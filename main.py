import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import NewClient
from crud import addNewClient, deleteClient, getClient, getClients, getCoffins, updateClient

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
    result = addNewClient(newClient)
    print("New client added with ID:", result)
    return {
        "success": True,
        "message": "Client added successfully",
        "client_id": result
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
    return updated_data

@app.get("/coffins")
def coffins():
    return getCoffins()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)