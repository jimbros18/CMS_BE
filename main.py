from urllib import response
from fastapi import Request
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from models import LoginPayload, NewClient
from crud import addNewClient, deleteClient, getClient, getClients, getCoffins, updateClient, getPlans, getAllLights, getAsstProviders, getallclientInfos, sign_in, require_role
from config import SUPABASE_URL, SUPABASE_KEY



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.post("/refresh_token")
async def refresh_token(request: Request):
    try:
        body = await request.json()
        refresh_token = body.get('refresh_token')
        res = supabase.auth.refresh_session(refresh_token)

        profile = supabase.table('profiles').select('username, branch, role').eq('email', res.user.email).execute()
        profile_data = profile.data[0] if profile.data else {}

        return {
            'token': res.session.access_token,
            'refresh_token': res.session.refresh_token,
            'user': res.user.email,
            'username': profile_data.get('username', ''),
            'branch': profile_data.get('branch', ''),
            'role': profile_data.get('role', '')
        }
    
    except Exception as e:
        raise HTTPException(status_code=401, detail="Session expired")

@app.post("/sign_in")
async def sign_in_endpoint(login_payload: LoginPayload):
    try:
        res = sign_in(supabase, login_payload.email, login_payload.password)
        
        if res.get('status') == 'success':            
            response = JSONResponse(content=res)
            response.set_cookie(
                        key="isAuthenticated",
                        value="true",
                        path="/",
                        httponly=False,
                        samesite="lax",  # Use 'lax' since it's same origin with proxy
                        secure=False,
                        max_age=60*60*24*7,
                    )
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
    print('raw: ', newClient)
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
async def delete_client(client_id: int, token_data: dict = Depends(require_role(['admin'], supabase))):
    deleteClient(client_id)
    return f"{client_id} deleted successfully"

@app.get("/getclient/{client_id}")
def get_client(client_id: int):
    client = getClient(client_id)
    return client

@app.put("/~client/{client_id}")
def update_client(client_id: int, payload: dict, token_data: dict = Depends(require_role(['admin', 'moderator'], supabase))):
    try:
        updated_data = updateClient(client_id, payload)
        print(updated_data)
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

@app.get("/asst_providers")
def providers():
    return getAsstProviders()

@app.get("/clients/charges")
def allclientInfos():
    data = getallclientInfos()
    return data

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)