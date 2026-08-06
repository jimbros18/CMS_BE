from dotenv import load_dotenv
import os
import requests
from fastapi import HTTPException, Request
from utils import parser, client_parser

load_dotenv()
db_url = os.getenv("DB_URL")
db_token = os.getenv("DB_TOKEN")

headers = {
    "Authorization": f"Bearer {db_token}",
    "Content-Type": "application/json"
}



def Clients():
    sql = """
        SELECT clients.id, 
            dateServiced, 
            deceasedFirst, 
            deceasedLast, 
            barangay,
            city, 
            province,
            plan, 
            coffin,
            embalmer,
            interment_datetime,
            COALESCE(p.total_paid, 0) + COALESCE(a.total_asst, 0) AS total_paid,
            (coffinAmount + COALESCE(oc.total_oc, 0)) 
                - (COALESCE(p.total_paid, 0) + COALESCE(a.total_asst, 0)) AS balance
        FROM clients
        LEFT JOIN (
            SELECT client_id, SUM(amount_paid) AS total_paid
            FROM payments
            GROUP BY client_id
        ) p ON clients.id = p.client_id
        LEFT JOIN (
            SELECT client_id, SUM(amount) AS total_oc
            FROM other_charges
            GROUP BY client_id
        ) oc ON clients.id = oc.client_id
        LEFT JOIN (
            SELECT client_id, SUM(amount) AS total_asst
            FROM assistance
            GROUP BY client_id
        ) a ON clients.id = a.client_id
        LEFT JOIN (
            SELECT client_id, embalmer 
            FROM staff
            GROUP BY client_id
        ) s ON clients.id = s.client_id
    """
    payload = {
        "requests": [{
            "type": "execute",
            "stmt": {"sql": sql, "args": []}
        }]
    }
    response = None
    try:
        response = requests.post(db_url, headers=headers, json=payload)
        response.raise_for_status()
        return parser(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def Client(id):
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT * FROM clients WHERE id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT * FROM payments WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT * FROM other_charges WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT * FROM assistance WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT * FROM inc_accessories WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT embalmer, driver, helper, plate_num FROM staff WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT lights FROM staff WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            },
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT returned FROM staff WHERE client_id = ?",
                    "args": [{"type": "integer", "value": str(id)}]
                }
            }
        ]
    }
    response = None
    try:
        response = requests.post(db_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()  # Parse once
        results = data["results"]
        
        client = client_parser({
            "client": results[0]["response"]["result"]["rows"],
            "payments": results[1]["response"]["result"]["rows"],
            "otherCharges": results[2]["response"]["result"]["rows"],
            "assistance": results[3]["response"]["result"]["rows"],
            "inclussions": results[4]["response"]["result"]["rows"],
            "staff": results[5]["response"]["result"]["rows"],
            "lights": results[6]["response"]["result"]["rows"],
            "returned": results[7]["response"]["result"]["rows"]
        })
        print("Client : ", client)  # Debugging line
        return client
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def Coffins():
    payload = {
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": "SELECT * FROM coffins",
                    "args": []
                }
            }
        ]
    }
    response = None
    try:
        response = requests.post(db_url, headers=headers, json=payload)
        response.raise_for_status()
        print("Coffins data: ", response.json())
        return parser(response)
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# def Client(id):
#     payload = {
#         "requests": [
#             {
#                 "type": "execute",
#                 "stmt": {
#                     "sql": "SELECT * FROM clients WHERE id = ?",
#                     "args": [{"type": "integer", "value": str(id)}]
#                 }
#             }
#         ]
#     }
    
#     try:
#         response = requests.post(db_url, headers=headers, json=payload)
#         print(f"Status: {response.status_code}")
#         print(f"Response Headers: {response.headers}")
#         print(f"Response Body: {response.text}")
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         print(f"❌ Error: {e}")
#         if hasattr(e, 'response') and e.response:
#             print(f"Error Response: {e.response.text}")
#         raise HTTPException(status_code=500, detail=str(e))