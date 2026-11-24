from urllib import response
from fastapi import Request
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client
from models import LoginPayload, NewClient
from crud import addNewClient, deleteClient, getClient, getClients, getCoffins, getIncAccessories, updateClient, getPlans, getAllLights, getAsstProviders, getallclientInfos
from turso_con import Client, Clients, Coffins, Update
from config import SUPABASE_URL, SUPABASE_KEY
from pocketbase import PocketBase
from pocketbase.client import ClientResponseError


app = FastAPI()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)



# Routes
@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/me")
async def me(request: Request):
    cookie = request.cookies.get("isAuthenticated")
    if cookie == "true":
        return {"status": "authenticated"}
    raise HTTPException(status_code=401, detail="Not authenticated")

security = HTTPBearer()
PB_URL = "http://127.0.0.1:8090"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    pb = PocketBase(PB_URL)
    pb.auth_store.save(token, None)
    
    try:
        auth_data = pb.collection("users").auth_refresh()
        return auth_data.record
    except ClientResponseError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(required_roles: list):
    def role_checker(user_record = Depends(verify_token)):
        user_role = user_record.role 
        
        if user_role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user_record
    return role_checker

@app.post("/sign_out")
async def sign_out():
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie(
        key="isAuthenticated",
        path="/"
    )
    return response

@app.post("/+client")
async def add_client(newClient: NewClient):
    # print('raw: ', newClient)
    data = addNewClient(newClient)
    # print("New client added with ID:", data)
    return {
        "success": True,
        "message": "Client added successfully",
        "client_id": data
    }

@app.get("/*clients")
def get_clients():
    clients = getClients()
    return {"clients": clients} 

@app.delete("/-client/{client_id}")
async def delete_client(client_id: int, user = Depends(require_role(['admin', 'developer']))):
    deleteClient(client_id)
    return {"message": f"{client_id} deleted successfully by {user.email}"}

@app.get("/getclient/{client_id}")
def get_client(client_id: int):
    client = getClient(client_id)
    return client

@app.put("/~client/{client_id}")
def update_client(client_id: int, payload: dict, user = Depends(require_role(['admin', 'moderator']))):
    print('PAYLOAD_INCs: ', payload['inclussions'])
    try:
        updated_data = updateClient(client_id, payload)
        return updated_data
    except Exception as e:
        print("error:", e)
        import traceback
        traceback.print_exc()
        raise

@app.get("/coffins")
def coffins():
    return getCoffins()


@app.get("/plans")
def plans():
    return getPlans()

@app.get("/lights")
def lights():
    return getAllLights()

@app.get("/inc_accessories/{client_id}")
def inc_accessories(client_id: int):
    return getIncAccessories(client_id)

@app.get("/asst_providers")
def providers():
    return getAsstProviders()

@app.get("/clients/charges")
def allclientInfos():
    data = getallclientInfos()
    return data

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)