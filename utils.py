def split_payload(client_id: int, payload: dict, old: dict):
    new = payload
    new_client_data = {'client_id': client_id}

    new_data = payload.get('client', {})
    old_data = old.get('client', {})
    keys = set(new_data.keys()) | set(old_data.keys())

    ### ======================= CLIENT ==============================
    if 'modified' not in new_client_data:
        new_client_data['modified'] = {}

    client_changes = {}
    for key in keys:
        new_val = new_data.get(key)
        old_val = old_data.get(key)
        if new_val != old_val:
            client_changes[key] = new_val

    if client_changes:
        new_client_data['modified']['client'] = client_changes
    
    ### ======================= OTHER CHARGES ==============================
    new_oc = new.get('otherCharges', [])
    old_oc = old.get('otherCharges', [])
    new_incs = new.get('inclusions', [])
    old_incs = old.get('inclusions', [])


    # Items in new but not in old → insert
    inserted_incs = [i for i in new_incs if i not in old_incs]
    if inserted_incs:
        if 'inserted' not in new_client_data:
            new_client_data['inserted'] = {}
        new_client_data['inserted']['inclusions'] = inserted_incs

    # Items in old but not in new → delete
    deleted_incs = [i for i in old_incs if i not in new_incs]
    if deleted_incs:
        if 'deleted' not in new_client_data:
            new_client_data['deleted'] = {}
        new_client_data['deleted']['inclusions'] = deleted_incs

    # DELETE
    deleted_oc_ids = {i["id"] for i in old_oc if "id" in i} - {i["id"] for i in new_oc if "id" in i}
    if deleted_oc_ids:
        if 'deleted' not in new_client_data:
            new_client_data['deleted'] = {}
        new_client_data['deleted']['otherCharges'] = list(deleted_oc_ids)

    # INSERT
    new_oc_items = [i for i in new_oc if 'id' not in i]
    if new_oc_items:
        if 'inserted' not in new_client_data:
            new_client_data['inserted'] = {}
        new_client_data['inserted']['otherCharges'] = list(new_oc_items)
    
    ### ======================= PAYMENTS ==============================================
    new_payments = new.get('payments', [])
    old_payments = old.get('payments', [])

    # DELETE
    deleted_payment_ids = {i["id"] for i in old_payments if "id" in i} - {i["id"] for i in new_payments if "id" in i}
    if deleted_payment_ids:
        if 'deleted' not in new_client_data:
            new_client_data['deleted'] = {}
        new_client_data['deleted']['payments'] = list(deleted_payment_ids)

    # INSERT
    new_payment_items = [i for i in new_payments if 'id' not in i]
    if new_payment_items:
        if 'inserted' not in new_client_data:
            new_client_data['inserted'] = {}
        new_client_data['inserted']['payments'] = list(new_payment_items)

    ### ======================= DSWD ================================================
    if new.get('dswd', []) != old.get('dswd', []):
        if 'modified' not in new_client_data:
            new_client_data['modified'] = {}
        new_client_data['modified']['dswd'] = new.get("dswd", [])

    ### ======================= STAFF =========================================
    new_staff_raw = new.get('staff', [])
    new_staff = new_staff_raw[0] if isinstance(new_staff_raw, list) and new_staff_raw else {}
    
    old_staff_raw = old.get('staff', [])
    old_staff = old_staff_raw[0] if isinstance(old_staff_raw, list) and old_staff_raw else {}

    if any(v for v in new_staff.values()) and new_staff != old_staff:
        if 'modified' not in new_client_data:
            new_client_data['modified'] = {}
        new_client_data['modified']['staff'] = new_staff

    ### ======================= LIGHTS =========================================
    new_lights = new.get('lights', [])
    old_lights  = old.get('lights', [])

    if new_lights is None:
        return

    if new_lights != old_lights:
        if 'modified' not in new_client_data:
            new_client_data['modified'] = {}
        new_client_data['modified']['lights'] = new_lights
    
    new_returned = new.get('returned', [])
    old_returned = old.get('returned', [])

    if new_returned is None:
        return
    
    if new_returned != old_returned:
        if 'modified' not in new_client_data:
            new_client_data['modified'] = {}
        new_client_data['modified']['returned'] = new_returned
        print('returned: ', new_client_data['modified']['returned'])

    return new_client_data

def run_query(new_client_data: dict):
    if 'modified' in new_client_data:
        for k, v in new_client_data['modified'].get('client', {}).items():
            print(f"Update client: set {k} = {v} where id = {new_client_data['client_id']}")
    
    return "data updated successfully"
