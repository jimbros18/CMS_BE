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

## ====================ASSISTANCE==============================================
    new_asst = new.get('assistance', [])
    old_asst = old.get('assistance', [])

    # INSERT new ones (no id)
    new_asst_items = [i for i in new_asst if 'id' not in i]
    if new_asst_items:
        if 'inserted' not in new_client_data:
            new_client_data['inserted'] = {}
        new_client_data['inserted']['assistance'] = new_asst_items

    # DELETE removed ones
    deleted_asst_ids = {i["id"] for i in old_asst if "id" in i} - {i["id"] for i in new_asst if "id" in i}
    if deleted_asst_ids:
        if 'deleted' not in new_client_data:
            new_client_data['deleted'] = {}
        new_client_data['deleted']['assistance'] = list(deleted_asst_ids)

    # UPDATE existing ones
    modified_asst = [i for i in new_asst if 'id' in i]
    old_asst_dict = {i["id"]: i for i in old_asst if "id" in i}
    changed_asst = [i for i in modified_asst if i != old_asst_dict.get(i["id"])]
    if changed_asst:
        if 'modified' not in new_client_data:
            new_client_data['modified'] = {}
        new_client_data['modified']['assistance'] = changed_asst

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

def parser(response):
    result = response.json()['results'][0]['response']['result']
    cols = [c['name'] for c in result['cols']]
    return [
        [v.get('value') for v in row]
        for row in result['rows']
    ]

def client_parser(data):
    def parse_value(val):
        """Convert Turso value to Python type"""
        if not val:
            return None
        if val["type"] == "integer":
            return int(val["value"])
        elif val["type"] == "float":
            return float(val["value"])
        elif val["type"] == "text":
            return val["value"]
        elif val["type"] == "null":
            return None
        else:
            return val["value"]
    
    def parse_rows(rows, cols=None):
        """Convert Turso rows to list of dictionaries"""
        if not rows:
            return []
        
        result = []
        for row in rows:
            if cols:
                # If column names provided, return dict
                item = {}
                for i, val in enumerate(row):
                    if i < len(cols):
                        item[cols[i]] = parse_value(val)
                result.append(item)
            else:
                # Return raw parsed values
                result.append([parse_value(val) for val in row])
        return result
    
    # Define column names for each table
    client_cols = [
        "id", "dateServiced", "deceasedFirst", "deceasedLast", 
        "deceasedMiddle", "cellNumber", "facebook", "city", 
        "plan", "coffin", "coffinAmount", "notes", 
        "interment_datetime", "barangay", "purok", "province"
    ]
    
    payments_cols = ["id", "client_id", "date_paid", "amount_paid", "details"]
    other_charges_cols = ["id", "client_id", "item_service", "amount", "details"]
    assistance_cols = ["id", "client_id", "gl_date", "provider", "ci_number", "processor", "amount"]
    inclussions_cols = ["id", "client_id", "accessories"]
    staff_cols = ["embalmer", "driver", "helper", "plate_num"]
    
    # Parse each section
    client_rows = data.get("client", [])
    client = parse_rows(client_rows, client_cols)[0] if client_rows else None
    
    payments = parse_rows(data.get("payments", []), payments_cols)
    otherCharges = parse_rows(data.get("otherCharges", []), other_charges_cols)
    assistance = parse_rows(data.get("assistance", []), assistance_cols)
    inclussions = parse_rows(data.get("inclussions", []), inclussions_cols)
    
    # Parse staff
    staff_rows = data.get("staff", [])
    staff = None
    if staff_rows:
        staff_dict = {}
        for i, col in enumerate(staff_cols):
            if i < len(staff_rows[0]):
                staff_dict[col] = parse_value(staff_rows[0][i])
        staff = staff_dict
    
    # Parse lights (parse JSON string if needed)
    lights_rows = data.get("lights", [])
    lights = []
    if lights_rows and lights_rows[0]:
        lights_value = parse_value(lights_rows[0][0])
        try:
            lights = eval(lights_value) if lights_value else []
        except:
            lights = []
    
    # Parse returned (parse JSON string if needed)
    returned_rows = data.get("returned", [])
    returned = []
    if returned_rows and returned_rows[0]:
        returned_value = parse_value(returned_rows[0][0])
        try:
            returned = eval(returned_value) if returned_value else []
        except:
            returned = []
    
    return {
        "client": client,
        "payments": payments,
        "otherCharges": otherCharges,
        "assistance": assistance,
        "inclussions": inclussions,
        "staff": staff,
        "lights": lights,
        "returned": returned
    }
