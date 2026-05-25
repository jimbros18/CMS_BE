import sqlite3
from utils import run_query, split_payload

db_name = 'lafh_transactions_db.sqlite3'


def getClients():
    query = "SELECT id, dateServiced, deceasedFirst, deceasedLast, deceasedMiddle, address, plan, coffin FROM clients"
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(query)
        clients = cursor.fetchall()
    return clients

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

    dswd = data_dict.get('dswd', [])
    otherCharges = data_dict.get('otherCharges', [])
    payments = data_dict.get('payments', [])
    inclusions = data_dict.get('inclusions', [])


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

        if dswd:
            dswd_keys = {k: v for k, v in dswd.items() if v is not None}
            if not dswd_keys:
                return
            else:
                dswd_cols = ", ".join(dswd_keys.keys())
                dswd_placeholders = ", ".join("?" for _ in dswd_keys)
                dswd_sql = f"INSERT INTO dswd (client_id, {dswd_cols}) VALUES (?, {dswd_placeholders})"
                dswd_vals = [client_id] + list(dswd_keys.values())
                cursor.execute(dswd_sql, dswd_vals)

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
    return data_dict
            
def updateClient(client_id: int, payload: dict):
    old_data = getClient(client_id)
    new_client_data = split_payload(client_id, payload, old_data)
    # print(f'payload: {payload}')

    if 'modified' in new_client_data and 'client' in new_client_data['modified']:
        up_client_tbl(client_id, new_client_data['modified']['client'])
    if 'modified' in new_client_data and 'dswd' in new_client_data['modified']:
        old_dswd = old_data.get('dswd', [])
        # print(f'dswd: {new_client_data["modified"]["dswd"]}')
        up_dswd_tbl(client_id, new_client_data['modified']['dswd'], old_dswd)

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

def up_client_tbl(client_id: int, client_kv: dict):
    print(f'client_kv: {client_kv}')
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
    
def up_dswd_tbl(client_id: int, dswd_kv: dict, old_dswd: dict):
    print(f'dswd_kv: {dswd_kv}')

    # 🔥 filter out unwanted keys too
    keys = {
        k: v for k, v in dswd_kv.items()
        if v is not None and k not in ('id', 'client_id')
    }

    if not keys:
        return

    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()

        if old_dswd:
            # ✅ UPDATE format
            cols = ", ".join(f"{k} = ?" for k in keys)
            sql = f"UPDATE dswd SET {cols} WHERE client_id = ?"
            vals = list(keys.values()) + [client_id]

        else:
            # ✅ INSERT format
            cols = ", ".join(keys.keys())
            placeholders = ", ".join("?" for _ in keys)
            sql = f"INSERT INTO dswd (client_id, {cols}) VALUES (?, {placeholders})"
            vals = [client_id] + list(keys.values())

        # print("SQL:", sql)
        # print("VALS:", vals)

        cursor.execute(sql, vals)
        connection.commit()

def deleteClient(client_id:int):
    sql = "DELETE FROM clients WHERE id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, (client_id,))

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

    sql4 = "SELECT * FROM dswd WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql4, (client_id,))
        raw_dswd = cursor.fetchall()
        dswd = [dict(d) for d in raw_dswd]

    sql5 = "SELECT item FROM inc_accessories WHERE client_id = ?"
    with sqlite3.connect(db_name, timeout=30) as connection:
        connection.row_factory = sqlite3.Row  # 👈 key line
        cursor = connection.cursor()
        cursor.execute(sql5, (client_id,))
        raw_inclusions = cursor.fetchall()
        inclusions = [i["item"] for i in raw_inclusions]

    return {"client": client, "otherCharges": otherCharges, "payments": payments, "dswd": dswd, "inclusions": inclusions}

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