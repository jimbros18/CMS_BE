from urllib import response
from fastapi import Request
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from models import LoginPayload, NewClient
from crud import addNewClient, deleteClient, getClient, getClients, getCoffins, updateClient, getPlans, getAllLights, getAsstProviders, getallclientInfos, sign_in
from dotenv import load_dotenv
import os



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug: Print environment variables (remove in production)
print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_KEY:", os.getenv("SUPABASE_KEY")[:10] + "..." if os.getenv("SUPABASE_KEY") else "Not found")



supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# print("SUPABASE_URL:", SUPABASE_URL)

app = FastAPI()

# CORS Configuration - MUST be the first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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

@app.post("/sign_in")
async def sign_in_endpoint(login_payload: LoginPayload):
    try:
        print(f"Login attempt for: {login_payload.email}")
        
        res = sign_in(supabase, login_payload.email, login_payload.password)
        print(f"Sign in result: {res}")
        
        if res.get('status') == 'success':
            response = JSONResponse(content={
                "status": "success",
                "message": "Login successful",
                "user": res.get('user')
            })
            
            # For proxy - same origin, so use lax
            response.set_cookie(
                key="isAuthenticated",
                value="true",
                path="/",
                httponly=False,
                samesite="lax",  # Use 'lax' since it's same origin with proxy
                secure=False,
                max_age=60*60*24*7,
                # NO domain specified - let browser handle it
            )
            
            print("Cookie SET for proxy")
            return response
        
        return JSONResponse(
            content={"status": "error", "message": res.get('message', 'Invalid credentials')},
            status_code=401
        )
        
    except Exception as e:
        print(f"Error in sign_in: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

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
    data = addNewClient(newClient)
    print("New client added with ID:", data)
    return {
        "success": True,
        "message": "Client added successfully",
    }

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
    print('updated: ', payload)
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

@app.get("/asst_providers")
def providers():
    return getAsstProviders()

@app.get("/clients/charges")
def allclientInfos():
    data = getallclientInfos()
    # print('Reports: ', data)
    return data

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)