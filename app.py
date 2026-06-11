from flask import Flask, jsonify, request, render_template, session
import proj2
import time

app = Flask(__name__)
app.secret_key = 'praan_core_super_secret_key'

# ==========================================
# AUTHENTICATION
# ==========================================
@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    if 'username' in session:
        return jsonify({"logged_in": True, "username": session['username'], "role": session.get('role')})
    return jsonify({"logged_in": False})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if username in proj2.admins and proj2.admins[username] == password:
        session['username'] = username
        session['role'] = 'admin'
        return jsonify({"success": True, "role": "admin", "message": "Admin login successful."})
    
    if username in proj2.users and proj2.users[username] == password:
        session['username'] = username
        session['role'] = 'user'
        return jsonify({"success": True, "role": "user", "message": "User login successful."})

    return jsonify({"success": False, "message": "Invalid username or password."})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."})
    if username in proj2.admins or username in proj2.users:
        return jsonify({"success": False, "message": "Username already exists."})

    proj2.users[username] = password
    proj2.user_penalties[username] = 0
    proj2.save_all_state()
    return jsonify({"success": True, "message": "User registered successfully."})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out."})

# ==========================================
# USER PORTAL API
# ==========================================
@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    username = session['username']
    penalty = proj2.user_penalties.get(username, 0)
    return jsonify({"success": True, "penalty": penalty})

@app.route('/api/user/pay', methods=['POST'])
def user_pay():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    username = session['username']
    penalty = proj2.user_penalties.get(username, 0)
    if penalty > 0:
        proj2.treasury_balance += penalty
        proj2.daily_revenue += penalty
        proj2.total_revenue += penalty
        proj2.user_penalties[username] = 0
        proj2.session_logs.append(f"User {username} paid penalty of ₹{penalty}")
        proj2.save_all_state()
        return jsonify({"success": True, "message": f"Successfully paid penalty of ₹{penalty}."})
    return jsonify({"success": False, "message": "No outstanding penalty."})

@app.route('/api/user/complaint', methods=['POST'])
def user_complaint():
    if 'username' not in session or session.get('role') != 'user':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    complaint = request.json.get('complaint', '').strip()
    if complaint:
        proj2.alert_logs.append(f"COMPLAINT from {session['username']}: {complaint}")
        proj2.show_alert(f"New User Complaint received", "WARNING", 5)
        proj2.save_all_state()
        return jsonify({"success": True, "message": "Complaint filed successfully."})
    return jsonify({"success": False, "message": "Complaint cannot be empty."})


@app.route('/')
def index():
    return render_template('index.html')

# ==========================================
# DASHBOARD & LOGS
# ==========================================
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    total_fill = sum(proj2.bin_fill.values())
    total_overflow = sum(proj2.overflow.values())
    active_bins = len([b for b in proj2.bin_fill if proj2.bin_fill[b] > 0])
    total_capacity = sum(f["capacity"] for f in proj2.processing_facilities.values())
    total_load = sum(f["current_load"] for f in proj2.processing_facilities.values())

    stats = {
        "treasury": proj2.treasury_balance,
        "revenue": proj2.daily_revenue,
        "expense": proj2.daily_expense,
        "total_waste": proj2.total_waste_collected,
        "total_fill": total_fill,
        "total_overflow": total_overflow,
        "active_bins": active_bins,
        "total_bins": len(proj2.bin_data),
        "total_capacity": total_capacity,
        "total_load": total_load,
        "weather_mode": proj2.weather_mode,
        "system_version": proj2.SYSTEM_VERSION
    }
    
    return jsonify({
        "stats": stats,
        "session_logs": proj2.session_logs[-15:],
        "alert_logs": proj2.alert_logs[-10:],
        "dispatch_logs": proj2.dispatch_logs[-10:]
    })

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    proj2.session_logs.clear()
    proj2.alert_logs.clear()
    proj2.dispatch_logs.clear()
    return jsonify({"success": True, "message": "All logs wiped from memory."})

@app.route('/api/admin/add', methods=['POST'])
def add_admin():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."})
    if username in proj2.admins or username in proj2.users:
        return jsonify({"success": False, "message": "Username already exists."})
        
    proj2.admins[username] = password
    proj2.save_all_state()
    proj2.session_logs.append(f"New admin registered: {username}")
    return jsonify({"success": True, "message": f"Admin {username} registered successfully."})

# ==========================================
# BINS & WASTE INJECTION
# ==========================================
@app.route('/api/bins', methods=['GET'])
def get_bins():
    bins = []
    for b in sorted(proj2.bin_data.keys()):
        area = proj2.bin_data[b]["area"]
        source = proj2.bin_data[b]["source"]
        bins.append({
            "id": b,
            "area": area,
            "source": source,
            "priority": proj2.category_priority[source],
            "fill": proj2.bin_fill[b],
            "max_limit": proj2.MAX_LIMIT,
            "overflow": proj2.overflow[b],
            "contaminated": proj2.contaminated[b],
            "active_vehicle": proj2.area_active_vehicle[area] or "None",
            "allowed_waste": proj2.allowed_waste[source]
        })
    return jsonify({"bins": bins, "areas": sorted(list(proj2.area_to_bins.keys()))})

@app.route('/api/bins/inject', methods=['POST'])
def inject_waste():
    data = request.json
    area = data.get("area", "").strip().upper()
    bin_id = data.get("bin_id", "").strip().upper()
    wtype = data.get("wtype", "").strip().upper()
    qty = float(data.get("qty", 0))
    
    if qty <= 0: return jsonify({"success": False, "message": "Quantity must be positive."})
    
    if bin_id not in proj2.bin_data:
        if area in proj2.area_to_bins:
            bin_id = proj2.area_to_bins[area][0] # Default to first bin if not specified
        else:
            return jsonify({"success": False, "message": "Invalid area or bin."})

    source = proj2.bin_data[bin_id]["source"]
    allowed = proj2.allowed_waste[source]
    warnings = []
    
    if wtype not in allowed:
        proj2.contaminated[bin_id] = True
        proj2.total_revenue += proj2.PENALTY
        proj2.daily_revenue += proj2.PENALTY
        proj2.treasury_balance += proj2.PENALTY
        proj2.session_logs.append(f"CONTAMINATION: {bin_id} | {wtype}")
        proj2.show_alert(f"CONTAMINATION detected in {bin_id}! Penalty applied.", "WARNING", 8)
        warnings.append(f"CONTAMINATION DETECTED: {wtype} is not allowed in {bin_id}.")
        
        # Penalize the currently logged-in user if any
        if session.get('role') == 'user':
            username = session['username']
            proj2.user_penalties[username] = proj2.user_penalties.get(username, 0) + proj2.PENALTY

    proj2.bin_subtypes[bin_id][wtype] = proj2.bin_subtypes[bin_id].get(wtype, 0) + qty
    proj2.bin_last_updated[bin_id] = time.time()

    if proj2.bin_fill[bin_id] + qty > proj2.MAX_LIMIT:
        proj2.overflow[bin_id] += (proj2.bin_fill[bin_id] + qty - proj2.MAX_LIMIT)
        proj2.bin_fill[bin_id] = proj2.MAX_LIMIT
        proj2.session_logs.append(f"OVERFLOW: {bin_id} has exceeded capacity")
        warnings.append(f"OVERFLOW DETECTED: {bin_id} capacity exceeded!")
    else:
        proj2.bin_fill[bin_id] += qty

    proj2.save_all_state()
    return jsonify({"success": True, "message": f"Successfully injected {qty}kg of {wtype} into {bin_id}.", "warnings": warnings})

# ==========================================
# DISPATCH & CLEARANCE
# ==========================================
@app.route('/api/dispatch/priority', methods=['POST'])
def dispatch_priority():
    filled = [b for b in proj2.bin_data if proj2.bin_fill[b] > 0 or proj2.overflow[b] > 0]
    if not filled:
        return jsonify({"success": False, "message": "All bins are empty. No dispatch required."})
    
    overflow_bins = [b for b in filled if proj2.overflow[b] > 0]
    critical_bins = [b for b in filled if proj2.overflow[b] == 0 and proj2.bin_fill[b] >= proj2.MAX_LIMIT * 0.9]
    normal_bins = [b for b in filled if proj2.overflow[b] == 0 and proj2.bin_fill[b] < proj2.MAX_LIMIT * 0.9]

    if overflow_bins: target = max(overflow_bins, key=lambda x: (proj2.category_priority[proj2.bin_data[x]["source"]], proj2.overflow[x]))
    elif critical_bins: target = max(critical_bins, key=lambda x: (proj2.category_priority[proj2.bin_data[x]["source"]], proj2.bin_fill[x]))
    else: target = max(normal_bins, key=lambda x: (proj2.category_priority[proj2.bin_data[x]["source"]], proj2.bin_fill[x]))

    area = proj2.bin_data[target]["area"]
    traffic = proj2.get_traffic_level(area)
    force_reroute = (traffic in ["VERY HIGH", "BLOCKED"] or area in proj2.road_closures)
    
    success = proj2.reduce_fuel(target, force_reroute=force_reroute)
    proj2.save_all_state()
    
    if success:
        return jsonify({"success": True, "message": f"Unit {target} cleared successfully."})
    else:
        return jsonify({"success": False, "message": f"Failed to clear {target}."})

@app.route('/api/dispatch/zone', methods=['POST'])
def dispatch_zone():
    data = request.json
    area = data.get("area", "").strip().upper()
    mode = data.get("mode", "standard").strip().lower()
    
    if area not in proj2.area_to_bins:
        return jsonify({"success": False, "message": "Area not recognized."})
        
    force_reroute = (mode == "reroute")
    different_vehicles = (mode == "different_vehicles")
    
    collected = proj2.collect_all_bins_in_area(area, force_reroute=force_reroute, different_vehicles=different_vehicles)
    proj2.save_all_state()
    
    mode_msg = ""
    if force_reroute: mode_msg = " with rerouting"
    elif different_vehicles: mode_msg = " using different vehicles"
    
    return jsonify({"success": True, "message": f"Zone clearance complete{mode_msg}. {collected} bins cleared in {area}."})

@app.route('/api/dispatch/bin', methods=['POST'])
def dispatch_bin():
    data = request.json
    bin_id = data.get("bin_id", "").strip().upper()
    
    if bin_id not in proj2.bin_data:
        return jsonify({"success": False, "message": "Bin ID not recognized."})
        
    area = proj2.bin_data[bin_id]["area"]
    traffic = proj2.get_traffic_level(area)
    force_reroute = (traffic in ["VERY HIGH", "BLOCKED"] or area in proj2.road_closures)
    
    success = proj2.reduce_fuel(bin_id, force_reroute=force_reroute)
    proj2.save_all_state()
    
    if success:
        return jsonify({"success": True, "message": f"Unit {bin_id} cleared successfully."})
    else:
        return jsonify({"success": False, "message": f"Failed to clear {bin_id}. It may be empty or vehicles are unavailable."})

@app.route('/api/dispatch/sweep', methods=['POST'])
def dispatch_sweep():
    data = request.json or {}
    force_reroute = data.get("reroute", False)
    total_cleared = 0
    for area in sorted(proj2.area_to_bins.keys()):
        if not force_reroute:
            proj2.optimize_route_for_zone(area)
        cleared = proj2.collect_all_bins_in_area(area, force_reroute=force_reroute)
        total_cleared += cleared
    proj2.save_all_state()
    
    msg = "Force reroute sweep complete" if force_reroute else "City sweep complete"
    return jsonify({"success": True, "message": f"{msg}. {total_cleared} bins processed."})

@app.route('/api/dispatch/reroute', methods=['POST'])
def dispatch_reroute():
    total_cleared = 0
    for area in proj2.area_to_bins.keys():
        cleared = proj2.collect_all_bins_in_area(area, force_reroute=True)
        total_cleared += cleared
    proj2.save_all_state()
    return jsonify({"success": True, "message": f"Force reroute complete. {total_cleared} bins cleared."})

# ==========================================
# FLEET & VEHICLES
# ==========================================
@app.route('/api/fleet', methods=['GET'])
def get_fleet():
    fleet = []
    for b in sorted(proj2.vehicles):
        area = proj2.bin_data[b]["area"]
        vtype = proj2.get_vehicle_type(b)
        role = "ACTIVE" if proj2.area_active_vehicle[area] == b else ("STANDBY" if b in proj2.area_vehicle_standby[area] else "IDLE")
        
        fleet.append({
            "id": b,
            "type": vtype,
            "area": area,
            "fuel": proj2.vehicles[b],
            "health": proj2.vehicle_health[b],
            "broken": proj2.vehicle_broken[b],
            "role": role
        })
    return jsonify({"fleet": fleet})

@app.route('/api/fleet/action', methods=['POST'])
def fleet_action():
    action = request.json.get("action")
    if action == "refuel":
        total_cost = sum((100 - proj2.vehicles[b]) * proj2.REFUEL_COST_PER_PERCENT for b in proj2.vehicles if proj2.vehicles[b] < 100)
        if total_cost > 0 and proj2.treasury_balance >= total_cost:
            for b in proj2.vehicles: proj2.vehicles[b] = 100.0
            proj2.treasury_balance -= total_cost
            proj2.daily_expense += total_cost
            proj2.save_all_state()
            return jsonify({"success": True, "message": f"All vehicles refueled. Cost: ₹{int(total_cost)}"})
        return jsonify({"success": False, "message": "Insufficient funds or already full."})
        
    elif action == "service":
        total_cost = sum((100 - proj2.vehicle_health[b]) * proj2.SERVICE_COST_PER_PERCENT for b in proj2.vehicle_health if proj2.vehicle_health[b] < 100)
        if total_cost > 0 and proj2.treasury_balance >= total_cost:
            for b in proj2.vehicle_health: 
                proj2.vehicle_health[b] = 100.0
                proj2.vehicle_broken[b] = False
            proj2.treasury_balance -= total_cost
            proj2.daily_expense += total_cost
            proj2.save_all_state()
            return jsonify({"success": True, "message": f"Fleet serviced. Cost: ₹{int(total_cost)}"})
        return jsonify({"success": False, "message": "Insufficient funds or already serviced."})
        
    elif action == "repair":
        broken = [b for b in proj2.vehicle_broken if proj2.vehicle_broken[b]]
        total_cost = len(broken) * 250
        if total_cost > 0 and proj2.treasury_balance >= total_cost:
            for b in broken:
                proj2.vehicle_broken[b] = False
                proj2.vehicle_health[b] = max(proj2.vehicle_health[b], 60)
            proj2.treasury_balance -= total_cost
            proj2.daily_expense += total_cost
            proj2.save_all_state()
            return jsonify({"success": True, "message": f"Broken vehicles repaired. Cost: ₹{int(total_cost)}"})
        return jsonify({"success": False, "message": "No broken vehicles or insufficient funds."})
    
    return jsonify({"success": False, "message": "Invalid action."})

# ==========================================
# WEATHER & FACILITIES
# ==========================================
@app.route('/api/weather', methods=['GET'])
def get_weather():
    areas = []
    for area in sorted(proj2.coordinates):
        risk, weather = proj2.weather_risk_score(area)
        traffic = proj2.get_traffic_level(area)
        areas.append({
            "area": area,
            "condition": weather['condition'],
            "rain": weather['rain_mm'],
            "wind": weather['wind_kmph'],
            "temp": weather['temperature'],
            "traffic": traffic,
            "road_closed": area in proj2.road_closures
        })
    return jsonify({
        "areas": areas, 
        "mode": proj2.weather_mode,
        "calendar": proj2.get_calendar_status()[0]
    })

@app.route('/api/weather/toggle', methods=['POST'])
def toggle_weather_mode():
    if proj2.weather_mode == "MANUAL":
        proj2.weather_mode = "WINDY"
    else:
        proj2.weather_mode = "MANUAL"
    return jsonify({"success": True, "message": f"Weather mode switched to {proj2.weather_mode}"})

@app.route('/api/facilities', methods=['GET'])
def get_facilities():
    facilities = []
    for f_name, f_data in proj2.processing_facilities.items():
        facilities.append({
            "name": f_name.replace("_", " "),
            "raw_name": f_name,
            "status": f_data["status"],
            "current_load": f_data["current_load"],
            "capacity": f_data["capacity"],
            "temporary_storage": proj2.temporary_storage.get(f_name, 0),
            "waste_types": f_data["waste_types"],
            "cost_per_kg": f_data["cost_per_kg"]
        })
    return jsonify({"facilities": facilities})

@app.route('/api/facilities/clear', methods=['POST'])
def clear_facility():
    target = request.json.get("facility", "").upper().replace(" ", "_")
    if target == "ALL":
        for f in proj2.processing_facilities:
            proj2.processing_facilities[f]["current_load"] = 0
            proj2.temporary_storage[f] = 0
        proj2.save_all_state()
        return jsonify({"success": True, "message": "All processing facilities cleared."})
    
    matched = next((f for f in proj2.processing_facilities if target and target in f.upper()), None)
    if matched:
        proj2.processing_facilities[matched]["current_load"] = 0
        proj2.temporary_storage[matched] = 0
        proj2.save_all_state()
        return jsonify({"success": True, "message": f"{matched.replace('_', ' ')} cleared."})
    return jsonify({"success": False, "message": "Invalid facility name."})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
