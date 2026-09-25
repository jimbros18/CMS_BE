import requests
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("DB_URL")
db_token = os.getenv("DB_TOKEN")

headers = {
    "Authorization": f"Bearer {db_token}",
    "Content-Type": "application/json"
}

def update_staff(client_id: int, staff: dict):
    keys = {k: v for k, v in staff.items() if v is not None and k != 'id'}
    if not keys:
        return

    # check if row exists
    check_payload = {
        "requests": [{
            "type": "execute",
            "stmt": {
                "sql": "SELECT id FROM staff WHERE client_id = ?",
                "args": [{"type": "integer", "value": str(client_id)}]
            }
        }]
    }
    res = requests.post(db_url, headers=headers, json=check_payload)
    res.raise_for_status()
    rows = res.json()['results'][0]['response']['result']['rows']
    exists = len(rows) > 0

    if exists:
        cols = ", ".join(f"{k} = ?" for k in keys)
        args = [{"type": "text", "value": str(v)} for v in keys.values()]
        args.append({"type": "integer", "value": str(client_id)})
        sql = f"UPDATE staff SET {cols} WHERE client_id = ?"
    else:
        keys['client_id'] = client_id
        cols = ", ".join(keys.keys())
        placeholders = ", ".join("?" * len(keys))
        args = [{"type": "text", "value": str(v)} for v in keys.values()]
        sql = f"INSERT INTO staff ({cols}) VALUES ({placeholders})"

    payload = {
        "requests": [{
            "type": "execute",
            "stmt": {"sql": sql, "args": args}
        }]
    }
    res = requests.post(db_url, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()