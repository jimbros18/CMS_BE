import sqlite3
import json
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from utils import run_query, split_payload
from config import JWT_KEY, PUBLIC_KEY
import supabase

security = HTTPBearer()
db_name = 'lafh_transactions_db.sqlite3'

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    print("token received:", token[:20])
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["ES256"], audience="authenticated")
        print("payload:", payload)
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        print("JWT error:", e)
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(required_roles: list, supabase):
    def role_checker(token_data: dict = Depends(verify_token)):
        user_email = token_data.get('email')
        profile = supabase.table('profiles').select('role').eq('email', user_email).execute()
        role = profile.data[0]['role'] if profile.data else None
        print("user_email:", user_email)
        print("role:", role)
        print("required_roles:", required_roles)
        if role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token_data
    return role_checker

def sign_in(supabase, email: str, password: str):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # get profile data
        profile = supabase.table('profiles').select('role, username, branch').eq('email', email).execute()
        profile_data = profile.data[0] if profile.data else {}

        return {
            'status': 'success',
            'email': res.user.email,
            'token': res.session.access_token,
            'refresh_token': res.session.refresh_token,
            'username': profile_data.get('username', ''),
            'role': profile_data.get('role'),
            'branch': profile_data.get('branch', '')
        }
    
    except Exception as e:
        print("Supabase error:", e)
        raise HTTPException(status_code=401, detail="Invalid credentials")

def getClients():
    query = """SELECT clients.id, 
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
    
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        clients = cursor.fetchall()
    return clients

def getallclientInfos():
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        query = """
            SELECT id, dateServiced, deceasedFirst, deceasedLast, city, province, plan, coffin, coffinAmount FROM clients
            """
        cursor.execute(query)
        clients = [dict(c) for c in cursor.fetchall()]
        
        for client in clients:
            cursor.execute("SELECT * FROM other_charges WHERE client_id = ?", (client['id'],))
            client['otherCharges'] = [dict(oc) for oc in cursor.fetchall()]

        for client in clients:
            cursor.execute("SELECT * FROM inc_accessories WHERE client_id = ?", (client['id'],))
            client['inclusions'] = [dict(i) for i in cursor.fetchall()]
        
        return clients

def getClient(client_id: int):
    sql = "SELECT * FROM clients WHERE id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql, (client_id,))
        raw_client = cursor.fetchone()
        client = dict(raw_client) if raw_client else None

    sql2 = "SELECT * FROM other_charges WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql2, (client_id,))
        raw_oc = cursor.fetchall()
        otherCharges = [dict(oc) for oc in raw_oc]

    sql3 = "SELECT * FROM payments WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql3, (client_id,))
        raw_payments = cursor.fetchall()
        payments = [dict(p) for p in raw_payments]

    sql4 = "SELECT * FROM assistance WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql4, (client_id,))
        raw_assistance = cursor.fetchall()
        assistance = [dict(d) for d in raw_assistance]

    sql5 = "SELECT item FROM inc_accessories WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql5, (client_id,))
        raw_inclusions = cursor.fetchall()
        inclusions = [i["item"] for i in raw_inclusions]

    sql6 = "SELECT * FROM staff WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(sql6, (client_id,))
        raw_s = cursor.fetchall()
        staff = [dict(d) for d in raw_s]

    sql_lights = """
        SELECT value FROM json_each(
            (SELECT lights FROM staff WHERE client_id = ?)
        )
    """

    sql_returned = """
        SELECT value FROM json_each(
            (SELECT returned FROM staff WHERE client_id = ?)
        )
    """

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        
        cursor.execute(sql_lights, (client_id,))
        lights = [row[0] for row in cursor.fetchall()]
        
        cursor.execute(sql_returned, (client_id,))
        returned = [row[0] for row in cursor.fetchall()]

    return {"client": client, "otherCharges": otherCharges, "payments": payments, "assistance": assistance, "inclusions": inclusions, "staff": staff, "lights": lights, "returned": returned}

def addNewClient(data):
    data_dict = data.model_dump()  # ✅ convert to dict
    #// CLIENT
    newclient = data_dict['client']
    clientKeys = {k: v for k, v in newclient.items() if v is not None}
    if not clientKeys:
        return  # Nothing to update
    clientcols = ", ".join(clientKeys.keys())
    client_placeholders = ", ".join("?" for _ in clientKeys)
    client_sql = f"INSERT INTO clients ({clientcols}) VALUES ({client_placeholders})"
    clientvals = list(clientKeys.values())

    assistance = data_dict.get('assistance', [])
    otherCharges = data_dict.get('otherCharges', [])
    payments = data_dict.get('payments', [])
    inclusions = data_dict.get('inclusions', [])
    lights = data_dict.get('lights', [])
    staff = data_dict.get('staff', [])


    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(client_sql, clientvals)
        client_id = cursor.lastrowid  # Get the last inserted client ID for foreign key reference

        if inclusions:
            for inc in inclusions:
                cursor.execute(
                    "INSERT INTO inc_accessories (client_id, item) VALUES (?, ?)",
                    (client_id, inc)
                )

        if otherCharges:
            for oc in otherCharges:
                oc_keys = {k: v for k, v in oc.items() if v is not None}
                if not oc_keys:
                    continue
                if 'amount' not in oc_keys:
                    raise ValueError('otherCharges entry must include amount')

                oc_cols = ", ".join(oc_keys.keys())
                oc_placeholders = ", ".join("?" for _ in oc_keys)
                oc_sql = f"INSERT INTO other_charges (client_id, {oc_cols}) VALUES (?, {oc_placeholders})"
                oc_vals = [client_id] + list(oc_keys.values())
                cursor.execute(oc_sql, oc_vals)

        if assistance:
            for asst in assistance:
                asst_keys = {k: v for k, v in asst.items() if v is not None}
                if not asst_keys:
                    continue
                asst_cols = ", ".join(asst_keys.keys())
                asst_placeholders = ", ".join("?" for _ in asst_keys)
                asst_sql = f"INSERT INTO assistance (client_id, {asst_cols}) VALUES (?, {asst_placeholders})"
                asst_vals = [client_id] + list(asst_keys.values())
                cursor.execute(asst_sql, asst_vals)

        if payments:
            for p in payments:
                # Ensure we have the right keys
                p_keys = {k: v for k, v in p.items() if v is not None}

                if not p_keys:
                    continue

                mapped = {
                    "date_paid": p_keys.get("date_paid"),
                    "amount_paid": p_keys.get("amount_paid"),
                    "details": p_keys.get("details")
                }

                if not mapped["date_paid"] or not mapped["amount_paid"]:
                    continue

                cols = ", ".join(mapped.keys())
                placeholders = ", ".join("?" for _ in mapped)

                sql = f"""
                    INSERT INTO payments (client_id, {cols})
                    VALUES (?, {placeholders})
                """

                vals = [client_id] + list(mapped.values())
                cursor.execute(sql, vals)

        # combine lights and staff into one row
        staff_data = {}

        if staff:
            s = staff[0] if isinstance(staff, list) else staff
            staff_data.update({k: v for k, v in s.items() if v is not None})

        if lights:
            staff_data['lights'] = json.dumps(lights)

        if staff_data:
            cols = ", ".join(staff_data.keys())
            placeholders = ", ".join("?" for _ in staff_data)
            sql = f"INSERT INTO staff (client_id, {cols}) VALUES (?, {placeholders})"
            vals = [client_id] + list(staff_data.values())
            cursor.execute(sql, vals)

    return data_dict
            
def updateClient(client_id: int, payload: dict):
    old_data = getClient(client_id)
    new_client_data = split_payload(client_id, payload, old_data)

    if 'modified' in new_client_data and 'client' in new_client_data['modified']:
        up_client_tbl(client_id, new_client_data['modified']['client'])
    if 'inserted' in new_client_data and 'assistance' in new_client_data['inserted']:
        insert_assistance_tbl(client_id, new_client_data['inserted']['assistance'])
    if 'deleted' in new_client_data and 'assistance' in new_client_data['deleted']:
        delete_assistance_tbl(client_id, new_client_data['deleted']['assistance'])
    if 'modified' in new_client_data and 'assistance' in new_client_data['modified']:
        for asst in new_client_data['modified']['assistance']:
            update_assistance(client_id, asst, old_data.get('assistance', []))
    if 'modified' in new_client_data and 'staff' in new_client_data['modified']:
        update_staff(client_id, new_client_data['modified']['staff'])
    if 'modified' in new_client_data and 'lights' in new_client_data['modified']:
        update_lights(client_id, new_client_data['modified']['lights'])
    if 'modified' in new_client_data and 'returned' in new_client_data['modified']:
        update_returned(client_id, new_client_data['modified']['returned'])
    if 'inserted' in new_client_data and 'inclusions' in new_client_data['inserted']:
        insert_incs_tbl(client_id, new_client_data['inserted']['inclusions'])
    if 'inserted' in new_client_data and 'otherCharges' in new_client_data['inserted']:
        insert_oc_tbl(client_id, new_client_data['inserted']['otherCharges'])
    if 'inserted' in new_client_data and 'payments' in new_client_data['inserted']:
        insert_payments_tbl(client_id, new_client_data['inserted']['payments'])
    if 'deleted' in new_client_data and 'inclusions' in new_client_data['deleted']:
        delete_incs_tbl(client_id, new_client_data['deleted']['inclusions'])
    if 'deleted' in new_client_data and 'otherCharges' in new_client_data['deleted']:
        delete_oc_tbl(client_id, new_client_data['deleted']['otherCharges'])
    if 'deleted' in new_client_data and 'payments' in new_client_data['deleted']:
        delete_payments_tbl(client_id, new_client_data['deleted']['payments'])

    if new_client_data == old_data: return {'updated': 'false'}
    print('new_data', new_client_data)
    return {'updated': 'true'}

def update_staff(client_id: int, staff: dict):
    keys = {k: v for k, v in staff.items() if v is not None and k != 'id'}
    if not keys:
        return

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        
        # check if row exists
        cursor.execute("SELECT id FROM staff WHERE client_id = ?", (client_id,))
        exists = cursor.fetchone()

        if exists:
            cols = ", ".join(f"{k} = ?" for k in keys)
            sql = f"UPDATE staff SET {cols} WHERE client_id = ?"
            vals = list(keys.values()) + [client_id]
            cursor.execute(sql, vals)
        else:
            keys['client_id'] = client_id
            cols = ", ".join(keys.keys())
            placeholders = ", ".join("?" * len(keys))
            sql = f"INSERT INTO staff ({cols}) VALUES ({placeholders})"
            cursor.execute(sql, list(keys.values()))

        connection.commit()

def update_lights(client_id: int, lights: list):
    sql = "UPDATE staff SET lights = ? WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (json.dumps(lights), client_id))
        connection.commit()

def update_returned(client_id: int, returned: list):
    sql = "UPDATE staff SET returned = ? WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (json.dumps(returned), client_id))
        connection.commit()

def up_client_tbl(client_id: int, client_kv: dict):
    keys = {k: v for k, v in client_kv.items() if v is not None}
    
    if not keys:
        return  # Nothing to update

    cols = ", ".join(f"{k} = ?" for k in keys)
    sql = f"UPDATE clients SET {cols} WHERE id = ?"
    vals = list(keys.values()) + [client_id]

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, vals)
        connection.commit()

def insert_incs_tbl(client_id: int, new_incs: list):
    if not new_incs:
        return

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO inc_accessories (client_id, item) VALUES (?, ?)",
            [(client_id, inc) for inc in new_incs]
        )
        connection.commit()

def delete_incs_tbl(client_id: int, deleted_incs: list):
    if not deleted_incs:
        return

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.executemany(
            "DELETE FROM inc_accessories WHERE client_id = ? AND item = ?",
            [(client_id, inc) for inc in deleted_incs]
        )
        connection.commit()

def insert_oc_tbl(client_id: int, oc_list: list):
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()

        for oc_kv in oc_list:
            keys = {k: v for k, v in oc_kv.items() if v is not None}

            if not keys:
                continue  # skip, don't exit

            cols = ", ".join(keys.keys())
            placeholders = ", ".join("?" for _ in keys)

            sql = f"INSERT INTO other_charges (client_id, {cols}) VALUES (?, {placeholders})"
            vals = [client_id] + list(keys.values())

            cursor.execute(sql, vals)

        connection.commit()

def delete_oc_tbl(client_id: int, oc_ids: list):
    if not oc_ids:
        return  # Nothing to delete

    placeholders = ", ".join("?" for _ in oc_ids)
    sql = f"DELETE FROM other_charges WHERE id IN ({placeholders}) AND client_id = ?"
    vals = oc_ids + [client_id]

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, vals)
        connection.commit()

def insert_payments_tbl(client_id: int, payments_list: list):
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()

        for payments_kv in payments_list:
            keys = {k: v for k, v in payments_kv.items() if v is not None}

            if not keys:
                continue  # skip, don't exit

            cols = ", ".join(keys.keys())
            placeholders = ", ".join("?" for _ in keys)

            sql = f"INSERT INTO payments (client_id, {cols}) VALUES (?, {placeholders})"
            vals = [client_id] + list(keys.values())

            cursor.execute(sql, vals)

        connection.commit()

def delete_payments_tbl(client_id: int, payment_ids: list):
    if not payment_ids:
        return  # Nothing to delete

    placeholders = ", ".join("?" for _ in payment_ids)
    sql = f"DELETE FROM payments WHERE id IN ({placeholders}) AND client_id = ?"
    vals = payment_ids + [client_id]

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, vals)
        connection.commit()
    
def update_assistance(client_id: int, new_asst: dict, old_asst: dict):
    print(f'new_asst: {new_asst}')

    # 🔥 filter out unwanted keys too
    keys = {
        k: v for k, v in new_asst.items()
        if v is not None and k not in ('id', 'client_id')
    }

    if not keys:
        return

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()

        if old_asst:
            # ✅ UPDATE format
            cols = ", ".join(f"{k} = ?" for k in keys)
            sql = f"UPDATE assistance SET {cols} WHERE client_id = ?"
            vals = list(keys.values()) + [client_id]

        else:
            # ✅ INSERT format
            cols = ", ".join(keys.keys())
            placeholders = ", ".join("?" for _ in keys)
            sql = f"INSERT INTO assistance (client_id, {cols}) VALUES (?, {placeholders})"
            vals = [client_id] + list(keys.values())

        # print("SQL:", sql)
        # print("VALS:", vals)

        cursor.execute(sql, vals)
        connection.commit()

def insert_assistance_tbl(client_id: int, items: list):
    if not items:
        return
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        for item in items:
            keys = {k: v for k, v in item.items() if k not in ('id', 'client_id')}
            cols = ", ".join(keys.keys())
            placeholders = ", ".join("?" * len(keys))
            sql = f"INSERT INTO assistance (client_id, {cols}) VALUES (?, {placeholders})"
            cursor.execute(sql, [client_id] + list(keys.values()))
        connection.commit()

def delete_assistance_tbl(client_id: int, ids: list):
    if not ids:
        return
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.executemany(
            "DELETE FROM assistance WHERE client_id = ? AND id = ?",
            [(client_id, i) for i in ids]
        )
        connection.commit()

def deleteClient(client_id:int):
    sql = "DELETE FROM clients WHERE id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (client_id,))

def getCoffins():
    sql ="""
            SELECT c.coffin_name, c.amount, i.items
            FROM coffins c
            LEFT JOIN inclusions i ON c.inclusion_id = i.id;
        """
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql)
        raw_coffins = cursor.fetchall()
        coffins = [dict(c) for c in raw_coffins]
        # print(coffins)
    return coffins

def getPlans():
    sql = "SELECT * FROM plans"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql)
        raw_plans = cursor.fetchall()
        plans = [dict(p) for p in raw_plans]
    return plans

def getAllLights():
    sql = "SELECT * FROM lights"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql)
        raw_ls = cursor.fetchall()
        lights = [dict(l) for l in raw_ls]
    return lights

def getAsstProviders():
    sql = "SELECT provider FROM asst_providers"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql)
        raw_prov = cursor.fetchall()
        asst_providers = [dict(l) for l in raw_prov]
    return asst_providers