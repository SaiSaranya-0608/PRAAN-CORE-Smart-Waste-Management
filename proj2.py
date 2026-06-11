from math import dist
import os
import sys
import time
import json
import requests
import random
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime

# -------------------------------------------------------------------------
# ----------------------------- COLORS & STYLES ---------------------------
# -------------------------------------------------------------------------
SAFFRON = "\033[38;5;208m"; WHITE = "\033[97m"; GREEN = "\033[92m"
CYAN = "\033[96m"; YELLOW = "\033[93m"; PURPLE = "\033[95m"
RED = "\033[91m"; BLUE = "\033[94m"
ORANGE = "\033[38;5;214m"; BOLD, RESET = "\033[1m", "\033[0m"
MAGENTA = "\033[35m"
BLINK = "\033[5m"

# Alert levels
ALERT_CRITICAL = f"{BLINK}{RED}{BOLD}"
ALERT_WARNING = f"{YELLOW}{BOLD}"
ALERT_INFO = f"{CYAN}{BOLD}"

# -------------------------------------------------------------------------
# ----------------------------- SYSTEM CONFIG -----------------------------
# -------------------------------------------------------------------------
MAX_LIMIT = 200
PENALTY = 100
FUEL_COST = 5
REFUEL_COST_PER_PERCENT = 2
SERVICE_COST_PER_PERCENT = 3
SYSTEM_VERSION = "6.2.0-PRAAN-ULTIMATE"

WINDY_API_KEY = os.getenv("WINDY_API_KEY", "").strip()
CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY", "").strip()

category_priority = {
    "MEDICAL": 5, "INDUSTRIAL": 4, "RESIDENTIAL": 3,
    "COMMERCIAL": 2, "COASTAL": 1
}

allowed_waste = {
    "RESIDENTIAL": ["BIODEGRADABLE", "PLASTIC"],
    "MEDICAL": ["HAZARDOUS", "BIO-MEDICAL"],
    "INDUSTRIAL": ["CHEMICAL", "METAL"],
    "COMMERCIAL": ["PLASTIC", "PAPER"],
    "COASTAL": ["ORGANIC", "PLASTIC"]
}

bin_data = {
    "B-01": {"area": "MADIPAKKAM", "source": "RESIDENTIAL"},
    "B-02": {"area": "MADIPAKKAM", "source": "RESIDENTIAL"},
    "B-03": {"area": "MEENAMBAKAM", "source": "RESIDENTIAL"},
    "B-04": {"area": "MEENAMBAKAM", "source": "RESIDENTIAL"},
    "B-05": {"area": "KELAMBAKKAM", "source": "RESIDENTIAL"},
    "B-06": {"area": "BEACH STATION", "source": "COASTAL"},
    "B-07": {"area": "BEACH STATION", "source": "COASTAL"},
    "B-08": {"area": "PORUR", "source": "MEDICAL"},
    "B-09": {"area": "PORUR", "source": "MEDICAL"},
    "B-10": {"area": "TEYNAMPET", "source": "MEDICAL"},
    "B-11": {"area": "BESANT NAGAR", "source": "COASTAL"},
    "B-12": {"area": "TRIPLICANE", "source": "COASTAL"},
    "B-13": {"area": "AMBATTUR", "source": "INDUSTRIAL"},
    "B-14": {"area": "AMBATTUR", "source": "INDUSTRIAL"},
    "B-15": {"area": "GUINDY", "source": "INDUSTRIAL"},
    "B-16": {"area": "GUINDY", "source": "INDUSTRIAL"},
    "B-17": {"area": "PARRYS CORNER", "source": "COMMERCIAL"},
    "B-18": {"area": "T NAGAR", "source": "COMMERCIAL"},
    "B-19": {"area": "T NAGAR", "source": "COMMERCIAL"},
    "B-20": {"area": "T NAGAR", "source": "COMMERCIAL"}
}

coordinates = {
    "MADIPAKKAM": (12.9647, 80.1986), "MEENAMBAKAM": (12.9877, 80.1765),
    "KELAMBAKKAM": (12.7870, 80.2200), "BEACH STATION": (13.0896, 80.2906),
    "PORUR": (13.0352, 80.1588), "TEYNAMPET": (13.0418, 80.2341),
    "BESANT NAGAR": (13.0003, 80.2668), "TRIPLICANE": (13.0588, 80.2756),
    "AMBATTUR": (13.1143, 80.1548), "GUINDY": (13.0105, 80.2206),
    "PARRYS CORNER": (13.0878, 80.2785), "T NAGAR": (13.0418, 80.2337)
}

destinations = {
    "BIODEGRADABLE": (13.0500, 80.2500), "PLASTIC": (13.0600, 80.2700),
    "HAZARDOUS": (13.0200, 80.2100), "BIO-MEDICAL": (13.0200, 80.2100),
    "CHEMICAL": (13.1000, 80.1800), "METAL": (13.1000, 80.1800),
    "PAPER": (13.0600, 80.2700), "ORGANIC": (13.0500, 80.2500),
    "CONTAMINATED": (13.0250, 80.2150)
}

DEPOT = (13.0827, 80.2707)

treasury_balance = 10000
daily_revenue = 0
daily_expense = 0
total_revenue = 0
total_waste_collected = 0
total_emissions = 0
total_recycled = 0
total_landfill = 0
daily_processing_cost = 0

area_to_bins = {
    area: [b for b in bin_data if bin_data[b]["area"] == area]
    for area in set(info["area"] for info in bin_data.values())
}

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

def load_json(filename, default_data):
    filepath = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return default_data

system_stats = load_json("system_stats.txt", {
    "treasury_balance": 10000, "daily_revenue": 0, "daily_expense": 0,
    "total_revenue": 0, "total_waste_collected": 0, "total_emissions": 0,
    "total_recycled": 0, "total_landfill": 0, "daily_processing_cost": 0
})
treasury_balance = system_stats["treasury_balance"]
daily_revenue = system_stats["daily_revenue"]
daily_expense = system_stats["daily_expense"]
total_revenue = system_stats["total_revenue"]
total_waste_collected = system_stats["total_waste_collected"]
total_emissions = system_stats["total_emissions"]
total_recycled = system_stats["total_recycled"]
total_landfill = system_stats["total_landfill"]
daily_processing_cost = system_stats["daily_processing_cost"]

def save_all_state():
    def save_json(filename, data):
        filepath = os.path.join(STORAGE_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
    save_json("admins.txt", admins)
    save_json("users.txt", users)
    save_json("user_penalties.txt", user_penalties)
    save_json("bin_fill.txt", bin_fill)
    save_json("overflow.txt", overflow)
    save_json("contaminated.txt", contaminated)
    save_json("vehicles.txt", {
        "fuel": vehicles,
        "health": vehicle_health,
        "broken": vehicle_broken
    })
    save_json("processing_facilities.txt", processing_facilities)
    save_json("temporary_storage.txt", temporary_storage)
    
    global treasury_balance, daily_revenue, daily_expense, total_revenue
    global total_waste_collected, total_emissions, total_recycled, total_landfill, daily_processing_cost
    save_json("system_stats.txt", {
        "treasury_balance": treasury_balance, "daily_revenue": daily_revenue,
        "daily_expense": daily_expense, "total_revenue": total_revenue,
        "total_waste_collected": total_waste_collected, "total_emissions": total_emissions,
        "total_recycled": total_recycled, "total_landfill": total_landfill,
        "daily_processing_cost": daily_processing_cost
    })
    save_json("system_logs.txt", {
        "session_logs": session_logs,
        "alert_logs": alert_logs,
        "dispatch_logs": dispatch_logs
    })

bin_fill = load_json("bin_fill.txt", {b: 0 for b in bin_data})
overflow = load_json("overflow.txt", {b: 0 for b in bin_data})
contaminated = load_json("contaminated.txt", {b: False for b in bin_data})

bin_subtypes = {b: {} for b in bin_data}
bin_last_updated = {b: None for b in bin_data}

# VEHICLE MANAGEMENT
vehicles_data = load_json("vehicles.txt", {
    "fuel": {b: 100.0 for b in bin_data},
    "health": {b: 100.0 for b in bin_data},
    "broken": {b: False for b in bin_data}
})
vehicles = vehicles_data.get("fuel", {b: 100.0 for b in bin_data})
vehicle_health = vehicles_data.get("health", {b: 100.0 for b in bin_data})
vehicle_broken = vehicles_data.get("broken", {b: False for b in bin_data})

vehicle_current_task = {b: None for b in bin_data}
route_db = {b: (i + 1) * 2 for i, b in enumerate(bin_data)}

# Vehicle management - ONE ACTIVE VEHICLE PER AREA
area_active_vehicle = {area: None for area in area_to_bins.keys()}
area_vehicle_standby = {area: [] for area in area_to_bins.keys()}

system_logs_data = load_json("system_logs.txt", {"session_logs": [], "alert_logs": [], "dispatch_logs": []})
session_logs = system_logs_data.get("session_logs", [])
alert_logs = system_logs_data.get("alert_logs", [])
dispatch_logs = system_logs_data.get("dispatch_logs", [])

admins = load_json("admins.txt", {"Deeksha": "chess", "Aruna": "parrot", "Saranya": "iam"})
users = load_json("users.txt", {})
user_penalties = load_json("user_penalties.txt", {})

weather_mode = "WINDY"

vehicle_type_by_source = {
    "RESIDENTIAL": "GENERAL_TRUCK",
    "COMMERCIAL": "RECYCLING_VAN",
    "COASTAL": "COASTAL_TRUCK",
    "MEDICAL": "MEDICAL_VAN",
    "INDUSTRIAL": "INDUSTRIAL_TRUCK"
}

vehicle_compatibility = {
    "GENERAL_TRUCK": ["BIODEGRADABLE", "PLASTIC", "ORGANIC", "PAPER", "CONTAMINATED"],
    "RECYCLING_VAN": ["PLASTIC", "PAPER"],
    "COASTAL_TRUCK": ["ORGANIC", "PLASTIC", "CONTAMINATED"],
    "MEDICAL_VAN": ["HAZARDOUS", "BIO-MEDICAL", "CONTAMINATED"],
    "INDUSTRIAL_TRUCK": ["CHEMICAL", "METAL", "CONTAMINATED"]
}

vehicle_capacity_kg = {
    "GENERAL_TRUCK": 600,
    "RECYCLING_VAN": 450,
    "COASTAL_TRUCK": 500,
    "MEDICAL_VAN": 300,
    "INDUSTRIAL_TRUCK": 700
}

# PROCESSING FACILITIES
default_processing_facilities = {
    "COMPOST_PLANT_A": {
        "waste_types": ["BIODEGRADABLE", "ORGANIC"],
        "capacity": 2000,
        "current_load": 0,
        "processing_rate": 400,
        "cost_per_kg": 2,
        "emission_factor": 1.2,
        "status": "OPEN"
    },
    "COMPOST_PLANT_B": {
        "waste_types": ["BIODEGRADABLE", "ORGANIC"],
        "capacity": 2000,
        "current_load": 0,
        "processing_rate": 400,
        "cost_per_kg": 2,
        "emission_factor": 1.2,
        "status": "OPEN"
    },
    "RECYCLING_CENTER_A": {
        "waste_types": ["PLASTIC", "PAPER", "METAL"],
        "capacity": 3000,
        "current_load": 0,
        "processing_rate": 600,
        "cost_per_kg": 4,
        "emission_factor": 0.8,
        "status": "OPEN"
    },
    "RECYCLING_CENTER_B": {
        "waste_types": ["PLASTIC", "PAPER", "METAL"],
        "capacity": 3000,
        "current_load": 0,
        "processing_rate": 600,
        "cost_per_kg": 4,
        "emission_factor": 0.8,
        "status": "OPEN"
    },
    "HAZARDOUS_TREATMENT_A": {
        "waste_types": ["HAZARDOUS", "CHEMICAL", "BIO-MEDICAL"],
        "capacity": 1000,
        "current_load": 0,
        "processing_rate": 200,
        "cost_per_kg": 10,
        "emission_factor": 4.5,
        "status": "OPEN"
    },
    "HAZARDOUS_TREATMENT_B": {
        "waste_types": ["HAZARDOUS", "CHEMICAL", "BIO-MEDICAL"],
        "capacity": 1000,
        "current_load": 0,
        "processing_rate": 200,
        "cost_per_kg": 10,
        "emission_factor": 4.5,
        "status": "OPEN"
    },
    "METAL_RECOVERY_A": {
        "waste_types": ["METAL"],
        "capacity": 1500,
        "current_load": 0,
        "processing_rate": 300,
        "cost_per_kg": 3,
        "emission_factor": 0.5,
        "status": "OPEN"
    },
    "METAL_RECOVERY_B": {
        "waste_types": ["METAL"],
        "capacity": 1500,
        "current_load": 0,
        "processing_rate": 300,
        "cost_per_kg": 3,
        "emission_factor": 0.5,
        "status": "OPEN"
    },
    "BIO_MEDICAL_INCINERATOR_A": {
        "waste_types": ["BIO-MEDICAL"],
        "capacity": 800,
        "current_load": 0,
        "processing_rate": 150,
        "cost_per_kg": 12,
        "emission_factor": 5.0,
        "status": "OPEN"
    },
    "BIO_MEDICAL_INCINERATOR_B": {
        "waste_types": ["BIO-MEDICAL"],
        "capacity": 800,
        "current_load": 0,
        "processing_rate": 150,
        "cost_per_kg": 12,
        "emission_factor": 5.0,
        "status": "OPEN"
    },
    "INDUSTRIAL_TREATMENT_A": {
        "waste_types": ["CHEMICAL"],
        "capacity": 1200,
        "current_load": 0,
        "processing_rate": 250,
        "cost_per_kg": 8,
        "emission_factor": 3.5,
        "status": "OPEN"
    },
    "INDUSTRIAL_TREATMENT_B": {
        "waste_types": ["CHEMICAL"],
        "capacity": 1200,
        "current_load": 0,
        "processing_rate": 250,
        "cost_per_kg": 8,
        "emission_factor": 3.5,
        "status": "OPEN"
    },
    "SECONDARY_SEGREGATION_A": {
        "waste_types": ["CONTAMINATED"],
        "capacity": 500,
        "current_load": 0,
        "processing_rate": 100,
        "cost_per_kg": 6,
        "emission_factor": 2.0,
        "status": "OPEN"
    },
    "SECONDARY_SEGREGATION_B": {
        "waste_types": ["CONTAMINATED"],
        "capacity": 500,
        "current_load": 0,
        "processing_rate": 100,
        "cost_per_kg": 6,
        "emission_factor": 2.0,
        "status": "OPEN"
    }
}

processing_facilities = load_json("processing_facilities.txt", default_processing_facilities)
temporary_storage = load_json("temporary_storage.txt", {facility: 0 for facility in processing_facilities})

manual_weather = {
    area: {"condition": "CLEAR", "rain_mm": 0, "wind_kmph": 8, "temperature": 31}
    for area in coordinates
}

traffic_overrides = {}
road_closures = set()
holiday_cache = {}

# -------------------------------------------------------------------------
# ----------------------------- CALENDAR FUNCTIONS ------------------------
# -------------------------------------------------------------------------

def fetch_indian_holidays(year):
    if year in holiday_cache:
        return holiday_cache[year]

    if not CALENDARIFIC_API_KEY:
        session_logs.append(f"Calendarific API key not set. Using weekend-only calendar for {year}.")
        holiday_cache[year] = {}
        return {}

    try:
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            "api_key": CALENDARIFIC_API_KEY,
            "country": "IN",
            "year": year,
            "type": "national"
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            session_logs.append(f"Calendarific API failed (HTTP {response.status_code}). Using weekend-only mode.")
            holiday_cache[year] = {}
            return {}

        data = response.json()
        
        if data.get("error"):
            session_logs.append(f"Calendarific API error: {data.get('error', {}).get('message', 'Unknown error')}")
            holiday_cache[year] = {}
            return {}

        holiday_items = data.get("response", {}).get("holidays", [])
        holidays = {}
        
        for h in holiday_items:
            date_key = h.get("date", {}).get("iso")
            name = h.get("name", "Public Holiday")
            if date_key:
                holidays[date_key] = {"name": name, "type": "Holiday"}

        holiday_cache[year] = holidays
        
        if holidays:
            session_logs.append(f"Loaded {len(holidays)} holidays for {year} from Calendarific")
        else:
            session_logs.append(f"No holidays found for {year}. Using weekend-only mode.")
        
        return holidays

    except Exception as e:
        session_logs.append(f"Calendarific API error: {str(e)}. Using weekend-only mode.")
        holiday_cache[year] = {}
        return {}

def is_festival_season(holidays=None):
    year = time.localtime().tm_year
    holidays = holidays or fetch_indian_holidays(year)
    
    festival_keywords = [
        "Diwali", "Pongal", "Holi", "Christmas",
        "Eid", "Navratri", "Dussehra", "Ganesh",
        "Durga", "Raksha", "Janmashtami"
    ]
    
    for h in holidays.values():
        name = h.get("name", "")
        for f in festival_keywords:
            if f.lower() in name.lower():
                return True
    
    current_month = time.localtime().tm_mon
    if 10 <= current_month <= 12:
        return True
        
    return False

def get_calendar_status():
    now = time.localtime()
    year = now.tm_year
    date_key = time.strftime("%Y-%m-%d", now)
    weekday = now.tm_wday
    
    holidays = fetch_indian_holidays(year)
    
    if date_key in holidays:
        h = holidays[date_key]
        return "HOLIDAY", h.get("name", "Public Holiday")
    
    if weekday == 5:
        return "WEEKEND", "Saturday"
    if weekday == 6:
        return "WEEKEND", "Sunday"
    
    return "WORKING_DAY", "Normal working day"

# -------------------------------------------------------------------------
# ----------------------------- ALERT SYSTEM ------------------------------
# -------------------------------------------------------------------------

def show_alert(message, alert_type="CRITICAL", duration=10):
    if alert_type == "CRITICAL":
        color = ALERT_CRITICAL
        icon = "🔴 CRITICAL ALERT 🔴"
    elif alert_type == "WARNING":
        color = ALERT_WARNING
        icon = "⚠️ WARNING ⚠️"
    else:
        color = ALERT_INFO
        icon = "ℹ️ INFO"
    
    alert_msg = f"\n{color}{'='*80}{RESET}\n"
    alert_msg += f"{color}{icon}{RESET}\n"
    alert_msg += f"{color}{message}{RESET}\n"
    alert_msg += f"{color}{'='*80}{RESET}\n"
    
    print(alert_msg)
    alert_logs.append(f"[{alert_type}] {message}")
    time.sleep(duration)

def check_vehicle_health_alerts():
    for vehicle in vehicles:
        health = vehicle_health[vehicle]
        if health < 10 and not vehicle_broken[vehicle]:
            show_alert(f"VEHICLE {vehicle} HEALTH CRITICAL: {health}%\nArea: {bin_data[vehicle]['area']}\nImmediate maintenance required!", "CRITICAL", 10)
            vehicle_broken[vehicle] = True
        elif health < 20 and health >= 10:
            show_alert(f"VEHICLE {vehicle} LOW HEALTH: {health}%\nArea: {bin_data[vehicle]['area']}\nSchedule maintenance soon.", "WARNING", 10)

def check_area_fleet_status(area):
    area_vehicles = [b for b in bin_data if bin_data[b]["area"] == area]
    
    if len(area_vehicles) == 0:
        show_alert(f"AREA {area} HAS NO VEHICLES ASSIGNED!", "CRITICAL", 12)
        return True
    
    working_vehicles = []
    for v in area_vehicles:
        if not vehicle_broken[v] and vehicles[v] > 5:
            working_vehicles.append(v)
    
    if len(working_vehicles) == 0:
        show_alert(f"AREA {area} FLEET EXHAUSTED! All vehicles broken or out of fuel.", "CRITICAL", 12)
        return True
    
    if area_active_vehicle[area] is None and len(working_vehicles) > 0:
        area_active_vehicle[area] = working_vehicles[0]
        print(f" {GREEN}▶ Vehicle {working_vehicles[0]} set as ACTIVE for {area}{RESET}")
    
    return False

# -------------------------------------------------------------------------
# ----------------------------- UI ENGINE ---------------------------------
# -------------------------------------------------------------------------

def engine_ui(title="", hearts=0):
    os.system('cls' if os.name == 'nt' else 'clear')
    width = 120
    def center(txt, clr=RESET):
        spaces = (width - len(str(txt))) // 2
        if spaces < 0:
            spaces = 0
        print(" " * spaces + clr + str(txt) + RESET)

    print(f"{SAFFRON}\u2554{chr(9552)*160}\u2557{RESET}")
    center("         ██████╗ ██████╗  █████╗  █████╗ ███╗   ██╗", SAFFRON + BOLD)
    center("         ██╔══██╗██╔══██╗██╔══██╗██╔══██╗████╗  ██║", SAFFRON + BOLD)
    center("         ██████╔╝██████╔╝███████║███████║██╔██╗ ██║", WHITE + BOLD)
    center("         ██╔═══╝ ██╔══██╗██╔══██║██╔══██║██║╚██╗██║", WHITE + BOLD)
    center("         ██║     ██║  ██║██║  ██║██║  ██║██║ ╚████║", GREEN + BOLD)
    center("         ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝", GREEN + BOLD)
    center("         U R B A N   W A S T E   M A N A G E M E N T", YELLOW + BOLD)

    if title:
        print(f"{SAFFRON}\u2560{chr(9552)*150}\u2563{RESET}")
        center(f"{PURPLE}{BOLD}{title}{RESET}")

    if hearts > 0:
        heart_str = "💚 " * hearts
        center(f"{ORANGE}\U0001f511 ACCESS KEYS: {heart_str}{RESET}")

    print(f"{SAFFRON}\u255a{chr(9552)*150}\u255d{RESET}")

def display_admin_profile(username):
    profiles = {
        "Deeksha": {"role": "Chief Operations Officer", "id": "ADM-001"},
        "Aruna": {"role": "Logistics Supervisor", "id": "ADM-002"},
        "Saranya": {"role": "System Analyst", "id": "ADM-003"}
    }

    profile = profiles.get(username, {"role": "Administrator", "id": "ADM-000"})
    engine_ui("ACCESS GRANTED - ADMIN PROFILE")
    name_display = username.upper().center(13)

    photo_box = [
        "┌───────────────┐",
        "│               │",
        f"│{name_display}│",
        "│   PROFILE     │",
        "│               │",
        "└───────────────┘"
    ]

    info_box = [
        f"{BOLD}{CYAN}NAME     {RESET}: {GREEN}{username}{RESET}",
        f"{BOLD}{CYAN}ROLE     {RESET}: {YELLOW}{profile['role']}{RESET}",
        f"{BOLD}{CYAN}ADMIN ID {RESET}: {PURPLE}{profile['id']}{RESET}",
        f"{BOLD}{CYAN}STATUS   {RESET}: {GREEN}● ACTIVE{RESET}"
    ]

    def pad(text, total=55):
        return text + " " * (total - len(text))

    print(f"\n {CYAN}┌{'-'*150}┐{RESET}")
    for i in range(max(len(photo_box), len(info_box))):
        left = photo_box[i] if i < len(photo_box) else " " * 17
        right = info_box[i] if i < len(info_box) else ""
        print(f" {CYAN}│{RESET}  {left}   {pad(right)}  {CYAN}│{RESET}")
    print(f" {CYAN}└{'-'*150}┘{RESET}")

    print(f"\n {CYAN}[1] ENTER COMMAND CENTER{RESET}")
    print(f" {RED}[0] LOGOUT{RESET}")

    while True:
        choice = input(f"\n {BOLD}{SAFFRON}SELECT OPTION > {RESET}")
        if choice == "1":
            return True
        elif choice == "0":
            return False
        else:
            print(f" {RED}INVALID INPUT. TRY AGAIN.{RESET}")

def display_user_profile(username):
    engine_ui("ACCESS GRANTED - USER PROFILE")
    name_display = username.upper().center(13)

    photo_box = [
        "┌───────────────┐",
        "│               │",
        f"│{name_display}│",
        "│   CITIZEN     │",
        "│               │",
        "└───────────────┘"
    ]

    info_box = [
        f"{BOLD}{CYAN}NAME     {RESET}: {GREEN}{username}{RESET}",
        f"{BOLD}{CYAN}ROLE     {RESET}: {YELLOW}Citizen / Resident{RESET}",
        f"{BOLD}{CYAN}ACCESS   {RESET}: {PURPLE}USER PORTAL{RESET}",
        f"{BOLD}{CYAN}STATUS   {RESET}: {GREEN}● ACTIVE{RESET}"
    ]

    def pad(text, total=55):
        return text + " " * (total - len(text))

    print(f"\n {CYAN}┌{'-'*150}┐{RESET}")
    for i in range(max(len(photo_box), len(info_box))):
        left = photo_box[i] if i < len(photo_box) else " " * 17
        right = info_box[i] if i < len(info_box) else ""
        print(f" {CYAN}│{RESET}  {left}   {pad(right)}  {CYAN}│{RESET}")
    print(f" {CYAN}└{'-'*150}┘{RESET}")
    time.sleep(1)

def show_jaihind():
    os.system('cls' if os.name == 'nt' else 'clear')
    width = 100
    def center(txt, clr=RESET):
        spaces = (width - len(str(txt))) // 2
        if spaces < 0:
            spaces = 0
        print(" " * spaces + clr + str(txt) + RESET)

    print(f"{WHITE}\n" * 2)
    center("   ██╗ ██████╗ ██╗", SAFFRON)
    center("   ██║ ██╔══██╗██║", SAFFRON)
    center("   ███████╔═██║██║", SAFFRON)
    center("   ██  ═██████║██║", SAFFRON)
    center("██╗██║  ██║██║ ██║", SAFFRON)
    center("  ╚═╝    ╚═╝╚═╝╚═╝", SAFFRON)
    center("██╗  ██╗██╗███╗   ██╗██████╗ ", WHITE)
    center("██║  ██║██║████╗  ██║██╔══██╗", WHITE)
    center("███████║██║██╔██╗ ██║██║  ██║ ", GREEN)
    center("██╔══██║██║██║╚██╗██║██║  ██║  ", GREEN)
    center("██║  ██║██║██║ ╚████║██████╔╝   ", GREEN)
    center("╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝    ╚", GREEN)

    print(f"\n")
    center("S Y S T E M   S H U T D O W N", RED + BOLD)
    center(f"Session Logs Exported. Final Revenue Projection: ₹{total_revenue}", BLUE)
    time.sleep(2)

def treasury_check():
    global treasury_balance
    if treasury_balance < 0:
        show_alert(f"FINANCIAL CRISIS! Treasury negative: ₹{treasury_balance}", "CRITICAL", 10)

def pause():
    input(f"\n{CYAN}PRESS ENTER TO CONTINUE...{RESET}")

# -------------------------------------------------------------------------
# ----------------------------- WEATHER FUNCTIONS -------------------------
# -------------------------------------------------------------------------

def get_traffic_level(area):
    if area in traffic_overrides:
        return traffic_overrides[area]

    now = time.localtime()
    hour = now.tm_hour
    weekday = now.tm_wday
    date_key = time.strftime("%Y-%m-%d", now)
    score = 0

    if 8 <= hour <= 10:
        score += 2
    if 17 <= hour <= 20:
        score += 3
    if weekday in [5, 6]:
        score += 2

    holidays = fetch_indian_holidays(now.tm_year)
    if date_key in holidays:
        score += 4
    if is_festival_season(holidays):
        score += 5
    if area in ["T NAGAR", "PARRYS CORNER", "BEACH STATION", "TRIPLICANE"]:
        score += 2

    if score >= 7:
        return "VERY HIGH"
    elif score >= 5:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    else:
        return "LOW"

def traffic_multiplier(level):
    return {
        "LOW": 1.0, "MEDIUM": 1.25, "HIGH": 1.6,
        "VERY HIGH": 2.0, "BLOCKED": 999
    }.get(level, 1.0)

def apply_area_microclimate(area, weather):
    adjusted = weather.copy()
    coastal_areas = ["BEACH STATION", "BESANT NAGAR", "TRIPLICANE"]
    commercial_areas = ["T NAGAR", "PARRYS CORNER"]
    industrial_areas = ["AMBATTUR", "GUINDY"]
    medical_areas = ["PORUR", "TEYNAMPET"]

    if area in coastal_areas:
        adjusted["wind_kmph"] += 8
        adjusted["rain_mm"] += 1.2
    if area in commercial_areas:
        adjusted["temperature"] += 1.5
    if area in industrial_areas:
        adjusted["temperature"] += 2.5
    if area in medical_areas:
        adjusted["temperature"] += 0.5

    if adjusted["rain_mm"] > 20 or adjusted["wind_kmph"] > 55:
        adjusted["condition"] = "STORM"
    elif adjusted["rain_mm"] > 8:
        adjusted["condition"] = "HEAVY_RAIN"
    elif adjusted["temperature"] > 38:
        adjusted["condition"] = "EXTREME_HEAT"
    elif adjusted["rain_mm"] > 0:
        adjusted["condition"] = "LIGHT_RAIN"
    else:
        adjusted["condition"] = "CLEAR"

    adjusted["rain_mm"] = round(adjusted["rain_mm"], 1)
    adjusted["wind_kmph"] = round(adjusted["wind_kmph"], 1)
    adjusted["temperature"] = round(adjusted["temperature"], 1)
    return adjusted

def get_area_weather(area):
    global weather_mode
    
    if weather_mode == "MANUAL":
        weather = apply_area_microclimate(area, manual_weather[area])
        weather["source"] = "MANUAL"
        return weather

    weather = apply_area_microclimate(area, manual_weather[area])
    weather["source"] = "MANUAL_FALLBACK"
    return weather

def weather_risk_score(area):
    weather = get_area_weather(area)
    risk = 0
    if weather["rain_mm"] > 8: risk += 20
    if weather["rain_mm"] > 20: risk += 20
    if weather["wind_kmph"] > 35: risk += 20
    if weather["wind_kmph"] > 55: risk += 25
    if weather["temperature"] > 38: risk += 10
    if weather["condition"] in ["STORM", "FLOOD"]: risk += 35
    return min(risk, 90), weather

def weather_fuel_multiplier(risk):
    return 1 + (risk / 200)

# -------------------------------------------------------------------------
# ----------------------------- VEHICLE AREA MANAGEMENT -------------------
# -------------------------------------------------------------------------

def get_active_vehicle_for_area(area):
    if area_active_vehicle[area] is not None:
        v = area_active_vehicle[area]
        if not vehicle_broken[v] and vehicles[v] > 20 and vehicle_health[v] > 20:
            return v
        else:
            area_active_vehicle[area] = None
            if v not in area_vehicle_standby[area]:
                area_vehicle_standby[area].append(v)
    
    if area_vehicle_standby[area]:
        new_active = area_vehicle_standby[area].pop(0)
        area_active_vehicle[area] = new_active
        print(f" {GREEN}▶ Vehicle {new_active} now ACTIVE for {area}{RESET}")
        return new_active
    
    area_vehicles = [b for b in bin_data if bin_data[b]["area"] == area]
    available = []
    
    for v in area_vehicles:
        if not vehicle_broken[v] and vehicle_current_task[v] is None:
            if vehicles[v] > 20 and vehicle_health[v] > 20:
                available.append(v)
    
    if available:
        available.sort(key=lambda x: vehicle_health[x], reverse=True)
        selected = available[0]
        area_active_vehicle[area] = selected
        print(f" {GREEN}▶ Vehicle {selected} now ACTIVE for {area}{RESET}")
        return selected
    
    return None

def release_vehicle(vehicle, area):
    vehicle_current_task[vehicle] = None
    
    if area_active_vehicle[area] == vehicle:
        area_active_vehicle[area] = None
        if not vehicle_broken[vehicle] and vehicles[vehicle] > 20 and vehicle_health[vehicle] > 20:
            if vehicle not in area_vehicle_standby[area]:
                area_vehicle_standby[area].append(vehicle)
                print(f" {BLUE}▶ Vehicle {vehicle} moved to STANDBY for {area}{RESET}")

def activate_next_vehicle(area):
    if area_active_vehicle[area] is None and area_vehicle_standby[area]:
        next_vehicle = area_vehicle_standby[area].pop(0)
        area_active_vehicle[area] = next_vehicle
        print(f" {GREEN}▶ Vehicle {next_vehicle} ACTIVATED for {area}{RESET}")
        return next_vehicle
    return None

def collect_all_bins_in_area(area, force_reroute=False, different_vehicles=False):
    bins_to_collect = [b for b in area_to_bins[area] if bin_fill[b] > 0 or overflow[b] > 0]
    
    if not bins_to_collect:
        print(f" {YELLOW}⚠️ No bins need collection in {area}{RESET}")
        return 0
    
    vehicle = get_active_vehicle_for_area(area)
    
    if not vehicle:
        show_alert(f"No vehicle available in {area}! Cannot collect bins.", "CRITICAL", 10)
        return 0
    
    print(f"\n {CYAN}{'='*80}{RESET}")
    print(f" {CYAN}🚛 AREA COLLECTION START: {area}{RESET}")
    print(f" {CYAN}Active Vehicle: {vehicle}{RESET}")
    print(f" {CYAN}Bins to collect: {len(bins_to_collect)}{RESET}")
    print(f" {CYAN}{'='*80}{RESET}")
    
    collected = 0
    
    for bin_id in bins_to_collect:
        print(f"\n {YELLOW}📦 Processing {bin_id}...{RESET}")
        
        if reduce_fuel(bin_id, assigned_vehicle=vehicle, force_reroute=force_reroute):
            bin_fill[bin_id] = 0
            overflow[bin_id] = 0
            bin_subtypes[bin_id] = {}
            contaminated[bin_id] = False
            collected += 1
            print(f" {GREEN}✓ {bin_id} cleared{RESET}")
        else:
            print(f" {RED}✗ {bin_id} failed{RESET}")
            if vehicle_broken[vehicle] or vehicles[vehicle] < 10 or vehicle_health[vehicle] < 10:
                show_alert(f"Vehicle {vehicle} failed during collection! Switching to standby.", "WARNING", 8)
                release_vehicle(vehicle, area)
                vehicle = activate_next_vehicle(area)
                if not vehicle:
                    print(f" {RED}No standby vehicle available! Stopping collection.{RESET}")
                    break
                else:
                    print(f" {GREEN}Continuing with vehicle {vehicle}{RESET}")
        
        if different_vehicles and collected < len(bins_to_collect):
            release_vehicle(vehicle, area)
            vehicle = activate_next_vehicle(area)
            if not vehicle:
                vehicle = get_active_vehicle_for_area(area)
            if not vehicle:
                print(f" {RED}No standby vehicle available for rotation! Stopping collection.{RESET}")
                break

        time.sleep(0.5)
    
    if vehicle:
        release_vehicle(vehicle, area)
    
    print(f"\n {GREEN}{'='*80}{RESET}")
    print(f" {GREEN}✅ AREA COLLECTION COMPLETE: {area}{RESET}")
    print(f" {GREEN}Collected: {collected}/{len(bins_to_collect)} bins{RESET}")
    print(f" {GREEN}{'='*80}{RESET}")
    
    return collected

# -------------------------------------------------------------------------
# ----------------------------- ROUTING FUNCTIONS -------------------------
# -------------------------------------------------------------------------

def get_route_distance(c1, c2):
    for attempt in range(3):
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{c1[1]},{c1[0]};{c2[1]},{c2[0]}?overview=false"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                time.sleep(1)
                continue
            data = response.json()
            if data.get("code") != "Ok":
                time.sleep(1)
                continue
            distance_km = round(data["routes"][0]["distance"] / 1000, 2)
            duration_min = int(data["routes"][0]["duration"] / 60)
            return distance_km, duration_min
        except Exception as e:
            if attempt == 2:
                session_logs.append(f"OSRM route error: {str(e)}")
            time.sleep(1)

    R = 6371
    lat1, lon1 = c1
    lat2, lon2 = c2
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    distance_km = round(R * 2 * atan2(sqrt(a), sqrt(1-a)), 2)
    duration_min = int(distance_km * 2)
    
    return distance_km, duration_min

def get_optimized_trip(coords_list):
    for attempt in range(3):
        try:
            coord_str = ";".join([f"{lon},{lat}" for lat, lon in coords_list])
            url = f"http://router.project-osrm.org/trip/v1/driving/{coord_str}?overview=false"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                time.sleep(1)
                continue
            data = response.json()
            if data.get("code") != "Ok":
                time.sleep(1)
                continue
            trip = data["trips"][0]
            return round(trip["distance"] / 1000, 2), int(trip["duration"] / 60), data
        except Exception as e:
            if attempt == 2:
                session_logs.append(f"OSRM trip error: {str(e)}")
            time.sleep(1)

    return 0.0, 0, None

def build_route_for_bins(bin_list):
    return [coordinates[bin_data[b]["area"]] for b in bin_list]

def get_priority_bins(limit=5):
    filled = [b for b in bin_data if bin_fill[b] > 0 or overflow[b] > 0]
    filled.sort(key=lambda x: (
        -overflow[x],
        -category_priority[bin_data[x]["source"]],
        -bin_fill[x]
    ))
    return filled[:limit]

def dominant_waste_type(b):
    if contaminated[b]:
        return "CONTAMINATED"
    if bin_subtypes[b]:
        return max(bin_subtypes[b], key=bin_subtypes[b].get)
    return allowed_waste[bin_data[b]["source"]][0]

def get_vehicle_type(vehicle_key):
    return vehicle_type_by_source[bin_data[vehicle_key]["source"]]

def is_vehicle_compatible(vehicle_key, waste_cat):
    vtype = get_vehicle_type(vehicle_key)
    return waste_cat in vehicle_compatibility[vtype]

def get_collection_deadline_hours(waste_cat):
    limits = {
        "ORGANIC": 24, "BIODEGRADABLE": 24, "BIO-MEDICAL": 12,
        "HAZARDOUS": 12, "CHEMICAL": 24, "PLASTIC": 72,
        "PAPER": 72, "METAL": 72, "CONTAMINATED": 8
    }
    return limits.get(waste_cat, 48)

def get_bin_age_hours(b):
    if not bin_last_updated[b]:
        return 0
    return round((time.time() - bin_last_updated[b]) / 3600, 2)

def get_time_constraint_status(b, waste_cat):
    age = get_bin_age_hours(b)
    limit = get_collection_deadline_hours(waste_cat)
    if age == 0: return "NO LOAD"
    if age >= limit: return "VIOLATION"
    if age >= limit * 0.75: return "URGENT"
    return "SAFE"

def vehicle_availability_score(vehicle_key, area):
    risk, _ = weather_risk_score(area)
    traffic = get_traffic_level(area)
    traffic_penalty = {"LOW": 0, "MEDIUM": 10, "HIGH": 20, "VERY HIGH": 35, "BLOCKED": 100}.get(traffic, 0)
    score = 100 - risk - traffic_penalty
    if vehicles[vehicle_key] < 20: score -= 30
    if vehicle_health[vehicle_key] < 30: score -= 35
    if vehicle_broken[vehicle_key]: score = 0
    return max(0, score)

def optimize_route_for_zone(area):
    bins_to_collect = [b for b in area_to_bins[area] if bin_fill[b] > 0 or overflow[b] > 0]
    
    if len(bins_to_collect) <= 1:
        return bins_to_collect
    
    coords = [coordinates[bin_data[b]["area"]] for b in bins_to_collect]
    dist_km, mins, _ = get_optimized_trip(coords)
    
    if dist_km > 0:
        print(f" {GREEN}📊 OPTIMIZED ROUTE: {len(bins_to_collect)} bins | Distance: {dist_km} km | Est Time: {mins} min{RESET}")
        
        single_trip_fuel = sum(route_db[b] for b in bins_to_collect) / 5
        optimized_fuel = dist_km / 5
        savings = single_trip_fuel - optimized_fuel
        
        if savings > 0:
            print(f" {GREEN}💰 FUEL SAVINGS: {savings:.1f} litres (₹{savings * FUEL_COST:.2f}){RESET}")
            session_logs.append(f"Route optimization for {area}: saved {savings:.1f}L fuel")
    
    return bins_to_collect

# -------------------------------------------------------------------------
# ----------------------------- FACILITY FUNCTIONS ------------------------
# -------------------------------------------------------------------------

def get_processing_facility(waste_cat):

    primary_map = {
        "BIODEGRADABLE": "COMPOST_PLANT_A",
        "ORGANIC": "COMPOST_PLANT_A",

        "PLASTIC": "RECYCLING_CENTER_A",
        "PAPER": "RECYCLING_CENTER_A",
        "METAL": "METAL_RECOVERY_A",

        "HAZARDOUS": "HAZARDOUS_TREATMENT_A",
        "BIO-MEDICAL": "BIO_MEDICAL_INCINERATOR_A",

        "CHEMICAL": "INDUSTRIAL_TREATMENT_A",

        "CONTAMINATED": "SECONDARY_SEGREGATION_A"
    }

    backup_map = {
        "BIODEGRADABLE": "COMPOST_PLANT_B",
        "ORGANIC": "COMPOST_PLANT_B",

        "PLASTIC": "RECYCLING_CENTER_B",
        "PAPER": "RECYCLING_CENTER_B",
        "METAL": "METAL_RECOVERY_B",

        "HAZARDOUS": "HAZARDOUS_TREATMENT_B",
        "BIO-MEDICAL": "BIO_MEDICAL_INCINERATOR_B",

        "CHEMICAL": "INDUSTRIAL_TREATMENT_B",

        "CONTAMINATED": "SECONDARY_SEGREGATION_B"
    }

    primary = primary_map.get(waste_cat)
    backup = backup_map.get(waste_cat)

    if primary:
        facility = processing_facilities[primary]

        if (
            facility["status"] == "OPEN"
            and facility["current_load"] < facility["capacity"]
        ):
            return primary

    if backup:
        facility = processing_facilities[backup]

        if (
            facility["status"] == "OPEN"
            and facility["current_load"] < facility["capacity"]
        ):
            print(f" {YELLOW}↪ Redirecting waste to backup facility: {backup}{RESET}")
            session_logs.append(f"Redirected {waste_cat} waste to backup facility {backup}")
            return backup

    return None

def send_to_facility(facility_name, waste_cat, qty):
    global total_emissions, total_recycled, total_landfill, daily_processing_cost, total_waste_collected

    if facility_name not in processing_facilities:
        return False

    facility = processing_facilities[facility_name]
    
    if waste_cat not in facility["waste_types"]:
        return False

    remaining = facility["capacity"] - facility["current_load"]

    if qty > remaining:
        accepted = remaining
        excess = qty - remaining
        facility["current_load"] = facility["capacity"]
        temporary_storage[facility_name] += excess
        total_waste_collected += accepted
        session_logs.append(f"Facility {facility_name} overflow: {excess}kg to storage")
    else:
        facility["current_load"] += qty
        total_waste_collected += qty

    daily_processing_cost += qty * facility["cost_per_kg"]
    total_emissions += qty * facility["emission_factor"]

    if "RECYCLING" in facility_name or "RECOVERY" in facility_name:
        total_recycled += qty
    elif "LANDFILL" in facility_name:
        total_landfill += qty

    session_logs.append(f"Sent {qty}kg of {waste_cat} to {facility_name}")
    return True

def process_facility_loads():
    for facility_name, facility in processing_facilities.items():
        processed = min(facility["processing_rate"], facility["current_load"])
        facility["current_load"] -= processed
        
        if temporary_storage[facility_name] > 0:
            from_storage = min(facility["processing_rate"] - processed, temporary_storage[facility_name])
            if from_storage > 0:
                temporary_storage[facility_name] -= from_storage
                facility["current_load"] = max(0, facility["current_load"] - from_storage)

def update_facility_failures():
    for facility_name, facility in processing_facilities.items():
        load_percent = (facility["current_load"] / facility["capacity"]) * 100 if facility["capacity"] > 0 else 0
        
        if load_percent >= 95:
            if facility["status"] == "OPEN":
                facility["status"] = "CLOSED"
                show_alert(f"FACILITY {facility_name} CLOSED due to 95% capacity!", "WARNING", 8)
        elif load_percent < 80:
            if facility["status"] == "CLOSED":
                facility["status"] = "OPEN"
                print(f" {GREEN}Facility {facility_name} reopened{RESET}")

def random_facility_shutdown():
    if random.randint(1, 50) == 1:
        facility = random.choice(list(processing_facilities.keys()))
        if processing_facilities[facility]["status"] == "OPEN":
            processing_facilities[facility]["status"] = "CLOSED"
            session_logs.append(f"RANDOM FACILITY FAILURE: {facility}")
            show_alert(f"RANDOM FAILURE: {facility} has shut down!", "CRITICAL", 10)

def show_processing_facilities():
    engine_ui("PROCESSING FACILITY STATUS")
    
    print(f"\n {SAFFRON}{'FACILITY':<28} {'WASTE TYPES':<32} {'LOAD':<15} {'STATUS':<10} {'STORAGE':<10} {'COST/kg':<10}{RESET}")
    print(f" {SAFFRON}{'─'*115}{RESET}")
    
    for facility_name, facility in processing_facilities.items():
        waste_types_str = ", ".join(facility["waste_types"][:2])
        if len(facility["waste_types"]) > 2:
            waste_types_str += f" +{len(facility['waste_types'])-2}"
        
        load_percent = (facility['current_load'] / facility['capacity']) * 100 if facility['capacity'] > 0 else 0
        load_text = f"{facility['current_load']:.0f}/{facility['capacity']}"
        
        if load_percent > 90:
            load_color = RED
        elif load_percent > 70:
            load_color = YELLOW
        else:
            load_color = GREEN
        
        status_color = GREEN if facility['status'] == 'OPEN' else RED
        
        display_name = facility_name[:26] + ".." if len(facility_name) > 28 else facility_name
        
        print(f"{CYAN}{display_name:<28}{RESET} "
              f"{WHITE}{waste_types_str:<32}{RESET} "
              f"{load_color}{load_text:<15}{RESET} "
              f"{status_color}{facility['status']:<10}{RESET} "
              f"{ORANGE}{temporary_storage[facility_name]:<10}{RESET} "
              f"{YELLOW}₹{facility['cost_per_kg']:<9}{RESET}")
    
    print(f"\n {BOLD}{CYAN}{'='*115}{RESET}")
    print(f" {BOLD}{CYAN}📊 FACILITY SUMMARY:{RESET}")
    
    total_capacity = sum(f["capacity"] for f in processing_facilities.values())
    total_load = sum(f["current_load"] for f in processing_facilities.values())
    total_storage = sum(temporary_storage.values())
    open_facilities = sum(1 for f in processing_facilities.values() if f["status"] == "OPEN")
    closed_facilities = len(processing_facilities) - open_facilities
    
    print(f"   {CYAN}Total Capacity:{RESET} {total_capacity:>8,} kg")
    print(f"   {CYAN}Current Load:{RESET}   {total_load:>8,.0f} kg ({total_load/total_capacity*100:.1f}%)")
    print(f"   {CYAN}Temporary Storage:{RESET} {total_storage:>8} kg")
    print(f"   {GREEN}Open Facilities:{RESET}   {open_facilities:>8}")
    print(f"   {RED}Closed Facilities:{RESET} {closed_facilities:>8}")
    
    util_percent = (total_load / total_capacity) * 100 if total_capacity > 0 else 0
    bar_length = 40
    filled = int(bar_length * util_percent / 100)
    bar = f"{GREEN}{'█' * filled}{RED}{'░' * (bar_length - filled)}{RESET}"
    print(f"   {CYAN}Utilization:{RESET} [{bar}] {util_percent:.1f}%")
    
    pause()

# -------------------------------------------------------------------------
# ----------------------------- DISPATCH FUNCTION (WITH REROUTE INFO) -----
# -------------------------------------------------------------------------

def reduce_fuel(b, assigned_vehicle=None, force_reroute=False):
    global treasury_balance, daily_expense, total_waste_collected

    if bin_fill[b] == 0 and overflow[b] == 0:
        print(f" {YELLOW}⚠️ SKIPPED: UNIT {b} IS ALREADY EMPTY.{RESET}")
        return False

    original_area = bin_data[b]["area"]
    current_area = original_area
    dispatch_start_time = time.time()
    was_rerouted = False
    alternative_area = None
    alternative_distance = 0
    original_distance_to_facility = 0

    waste_cat = dominant_waste_type(b)
    facility = get_processing_facility(waste_cat)

    if not facility:
        print(f" {RED}No open approved facility for {waste_cat}. Collection delayed.{RESET}")
        session_logs.append(f"No open facility for {waste_cat}")
        return False

    # Calculate ORIGINAL distance first (from bin's own area)
    original_dist, original_mins = get_route_distance(coordinates[original_area], destinations[waste_cat])
    if original_dist == 0:
        original_dist = route_db[b]
        original_mins = int(original_dist * 2)

    traffic = get_traffic_level(current_area)
    
    # REROUTE LOGIC - Find closest alternative area with available vehicle
    if traffic in ["VERY HIGH", "BLOCKED"] or current_area in road_closures or force_reroute:
        print(f" {YELLOW}🔄 Rerouting required for {b} (Traffic: {traffic}, Road closure: {current_area in road_closures}){RESET}")
        was_rerouted = True
        
        # Find the CLOSEST area with an available vehicle
        current_coord = coordinates[original_area]
        facility_coord = destinations[waste_cat]
        
        best_area = None
        best_vehicle = None
        best_total_distance = float('inf')
        best_alternative_distance = 0
        
        # Calculate distances to find closest area
        for area in coordinates:
            if area == original_area:
                continue
            if area in road_closures:
                continue
            
            # Check if this area has an available vehicle
            area_has_vehicle = False
            area_vehicle = None
            
            # Check active vehicle
            if area_active_vehicle[area] is not None:
                v = area_active_vehicle[area]
                if not vehicle_broken[v] and vehicles[v] > 20 and is_vehicle_compatible(v, waste_cat):
                    area_has_vehicle = True
                    area_vehicle = v
            
            # Check standby vehicles
            if not area_has_vehicle and area_vehicle_standby[area]:
                for v in area_vehicle_standby[area]:
                    if not vehicle_broken[v] and vehicles[v] > 20 and is_vehicle_compatible(v, waste_cat):
                        area_has_vehicle = True
                        area_vehicle = v
                        break
            
            # Check all vehicles in area
            if not area_has_vehicle:
                for v in [bv for bv in bin_data if bin_data[bv]["area"] == area]:
                    if not vehicle_broken[v] and vehicles[v] > 20 and is_vehicle_compatible(v, waste_cat):
                        area_has_vehicle = True
                        area_vehicle = v
                        break
            
            if area_has_vehicle:
                # Calculate distance from alternative area to bin
                alt_to_bin, _ = get_route_distance(coordinates[area], coordinates[original_area])
                # Calculate distance from bin to facility
                bin_to_facility, _ = get_route_distance(coordinates[original_area], facility_coord)
                # Total = alt_area → bin → facility
                total_dist = alt_to_bin + bin_to_facility
                
                if total_dist < best_total_distance:
                    best_total_distance = total_dist
                    best_area = area
                    best_vehicle = area_vehicle
                    best_alternative_distance = alt_to_bin
        
        if best_area and best_vehicle:
            current_area = best_area
            assigned_vehicle = best_vehicle
            alternative_area = best_area
            alternative_distance = best_alternative_distance
            
            print(f" {GREEN}▶ AUTOMATIC REROUTE: Using vehicle {best_vehicle} from {best_area}{RESET}")
            print(f" {GREEN}   Original area: {original_area} → Rerouted from: {best_area}{RESET}")
            print(f" {GREEN}   Distance from {best_area} to bin: {best_alternative_distance:.2f} km{RESET}")
            print(f" {GREEN}   Original distance from {original_area} to facility: {original_dist:.2f} km{RESET}")
            print(f" {GREEN}   Total reroute distance: {best_total_distance:.2f} km{RESET}")
            
            session_logs.append(f"Auto-rerouted {b}: {original_area} → {best_area} (alt dist: {best_alternative_distance:.1f}km)")
            show_alert(f"AUTO-REROUTING {b} from {best_area} (closest available)", "INFO", 5)
        else:
            print(f" {RED}No alternative area with available vehicle found!{RESET}")
            show_alert(f"UNABLE TO REROUTE {b} - No vehicles available in nearby areas", "WARNING", 5)

    check_area_fleet_status(current_area)

    risk, weather = weather_risk_score(current_area)

    # Get the distance based on current area (may be rerouted)
    if was_rerouted and current_area != original_area and alternative_area:
        # Calculate route from alternative area to bin to facility
        alt_to_bin, _ = get_route_distance(coordinates[current_area], coordinates[original_area])
        bin_to_facility, _ = get_route_distance(coordinates[original_area], destinations[waste_cat])
        base_dist = alt_to_bin + bin_to_facility
        base_mins = int(base_dist * 2)
    else:
        base_dist, base_mins = get_route_distance(coordinates[current_area], destinations[waste_cat])
        if base_dist == 0:
            base_dist = route_db[b]
            base_mins = int(base_dist * 2)
    
    actual_dist = round(base_dist * traffic_multiplier(traffic) * weather_fuel_multiplier(risk), 2)
    actual_mins = int(base_mins * traffic_multiplier(traffic))

    FUEL_CAPACITY = 100
    KM_PER_LITRE = 5
    fuel_used_litres = actual_dist / KM_PER_LITRE
    fuel_needed = (fuel_used_litres / FUEL_CAPACITY) * 100
    wear_tear = max(1, actual_dist * 0.3)

    if assigned_vehicle:
        vehicle_key = assigned_vehicle
    else:
        vehicle_key = get_active_vehicle_for_area(current_area)
    
    if not vehicle_key:
        print(f" {RED}Failed: no compatible available vehicle for {waste_cat} in {current_area}.{RESET}")
        session_logs.append(f"No vehicle available: {b} | {waste_cat} | {current_area}")
        return False

    vehicle_type = get_vehicle_type(vehicle_key)
    capacity = vehicle_capacity_kg[vehicle_type]
    load = bin_fill[b] + overflow[b]

    if load > capacity:
        print(f" {YELLOW}Load warning: {load:.1f} kg exceeds {vehicle_type} capacity {capacity} kg.{RESET}")

    vehicles[vehicle_key] -= fuel_needed
    if vehicles[vehicle_key] < 0:
        vehicles[vehicle_key] = 0
    
    vehicle_health[vehicle_key] -= wear_tear
    if vehicle_health[vehicle_key] < 0:
        vehicle_health[vehicle_key] = 0

    if vehicle_health[vehicle_key] <= 0 and not vehicle_broken[vehicle_key]:
        vehicle_broken[vehicle_key] = True
        show_alert(f"VEHICLE {vehicle_key} BROKE DOWN during collection!", "CRITICAL", 5)
        return False

    cost = actual_dist * FUEL_COST
    daily_expense += cost
    treasury_balance -= cost
    
    load_collected = bin_fill[b] + overflow[b]
    total_waste_collected += load_collected

    cal_status, cal_name = get_calendar_status()
    
    dispatch_end_time = time.time()
    dispatch_duration = round(dispatch_end_time - dispatch_start_time, 2)

    # Store dispatch log with reroute information
    dispatch_logs.append({
        "bin": b,
        "vehicle": vehicle_key,
        "area": current_area,
        "original_area": original_area,
        "waste_type": waste_cat,
        "base_time_min": base_mins,
        "actual_time_min": actual_mins,
        "time_difference": actual_mins - base_mins,
        "rerouted": was_rerouted,
        "rerouted_from_area": alternative_area if was_rerouted else None,
        "alternative_distance": alternative_distance if was_rerouted else 0,
        "original_distance": original_dist,
        "traffic_level": traffic,
        "weather_condition": weather['condition'],
        "distance_km": actual_dist,
        "cost": round(cost, 2),
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })

    # SEND TO FACILITY
    send_to_facility(facility, waste_cat, load_collected)

    print(f" {CYAN}📍 Route: {current_area} → {facility}{RESET}")
    print(f" {CYAN}🚛 Vehicle: {vehicle_key} ({vehicle_type}) | Bin: {b}{RESET}")
    print(f" {YELLOW}🚦 Traffic: {traffic} | 📅 Calendar: {cal_status}{RESET}")
    print(f" {PURPLE}🌤️ Weather: {weather['condition']} | Rain {weather['rain_mm']}mm | Wind {weather['wind_kmph']}km/h{RESET}")
    print(f" {BLUE}⏱️ BASE TIME: {base_mins} min | ACTUAL TIME: {actual_mins} min | DIFF: +{actual_mins - base_mins} min{RESET}")

    if was_rerouted and alternative_area:
        print(f" {ORANGE}🔄 REROUTED: Original area {original_area} → Vehicle from {alternative_area} (distance: {alternative_distance:.1f}km to bin){RESET}")
        print(f" {ORANGE}   Original distance to facility: {original_dist:.1f}km | Reroute total: {base_dist:.1f}km{RESET}")

    print(f" {GREEN}📏 Distance: {actual_dist} km | ⏱️ Dispatch Duration: {dispatch_duration}s | 💰 Cost: ₹{round(cost, 2)}{RESET}")

    session_logs.append(
        f"Dispatch: {vehicle_key} cleared {b} | {waste_cat} | {current_area} | "
        f"traffic:{traffic} | base:{base_mins}min actual:{actual_mins}min | reroute:{was_rerouted}"
    )

    treasury_check()
    check_vehicle_health_alerts()
    
    # Clear the bin after successful dispatch
    bin_fill[b] = 0
    overflow[b] = 0
    bin_subtypes[b] = {}
    contaminated[b] = False
    
    save_all_state()
    return True

def get_vehicle_operational_status(vehicle_key, target_bin):
    area = bin_data[target_bin]["area"]
    waste_cat = dominant_waste_type(target_bin)
    vtype = get_vehicle_type(vehicle_key)
    compatible = "YES" if is_vehicle_compatible(vehicle_key, waste_cat) else "NO"
    facility = get_processing_facility(waste_cat) or "NO FACILITY"
    traffic = get_traffic_level(area)
    risk, weather = weather_risk_score(area)
    availability = vehicle_availability_score(vehicle_key, area)
    time_status = get_time_constraint_status(target_bin, waste_cat)

    if vehicle_broken[vehicle_key]: dispatch_status = "BROKEN"
    elif area in road_closures: dispatch_status = "ROAD CLOSED"
    elif traffic == "BLOCKED": dispatch_status = "TRAFFIC BLOCK"
    elif compatible == "NO": dispatch_status = "INCOMPATIBLE"
    elif facility == "NO FACILITY": dispatch_status = "FACILITY CLOSED"
    elif vehicles[vehicle_key] < 20: dispatch_status = "LOW FUEL"
    elif vehicle_health[vehicle_key] < 20: dispatch_status = "MAINTENANCE"
    elif availability < 35: dispatch_status = "LOW AVAILABILITY"
    else: dispatch_status = "READY"

    return {
        "waste_cat": waste_cat, "vehicle_type": vtype, "compatible": compatible,
        "facility": facility, "traffic": traffic, "weather": weather["condition"],
        "weather_risk": risk, "availability": availability,
        "time_status": time_status, "dispatch_status": dispatch_status
    }

# -------------------------------------------------------------------------
# ----------------------------- USER FUNCTIONS ----------------------------
# -------------------------------------------------------------------------

def user_register():
    engine_ui("NEW USER REGISTRATION")
    print(f"\n {CYAN}CREATE YOUR ACCOUNT{RESET}\n")

    username = input(f" {CYAN}CHOOSE USERNAME : {RESET}").strip()
    if not username:
        print(f" {RED}❌ USERNAME CANNOT BE EMPTY.{RESET}"); time.sleep(1); return
    if username in users:
        print(f" {RED}❌ USERNAME ALREADY EXISTS.{RESET}"); time.sleep(1); return
    if username in admins:
        print(f" {RED}❌ THIS USERNAME IS RESERVED.{RESET}"); time.sleep(1); return

    password = input(f" {CYAN}SET PASSWORD    : {RESET}").strip()
    if not password:
        print(f" {RED}❌ PASSWORD CANNOT BE EMPTY.{RESET}"); time.sleep(1); return

    confirm = input(f" {CYAN}CONFIRM PASSWORD: {RESET}").strip()
    if password != confirm:
        print(f" {RED}❌ PASSWORDS DO NOT MATCH.{RESET}"); time.sleep(1); return

    users[username] = password
    user_penalties[username] = []
    save_all_state()
    session_logs.append(f"New user registered: {username}")
    print(f"\n {GREEN}✅ REGISTRATION SUCCESSFUL! WELCOME, {username.upper()}.{RESET}")
    time.sleep(1.5)

def user_login():
    attempts = 3
    while attempts > 0:
        engine_ui("USER SECURE LOGIN", hearts=attempts)
        u = input(f"  {CYAN}USERNAME: {RESET}").strip()
        p = input(f"  {CYAN}PASSWORD: {RESET}").strip()

        if users.get(u) == p:
            session_logs.append(f"User access granted: {u}")
            display_user_profile(u)
            user_panel(u)
            return
        attempts -= 1
        session_logs.append(f"Failed user login attempt: {u}")
        print(f"  {RED}❌ INVALID CREDENTIALS{RESET}")
        time.sleep(1)

    if attempts == 0:
        print(f" {RED}SECURITY LOCK: TOO MANY FAILED ATTEMPTS.{RESET}")
        time.sleep(2)

def user_panel(username):
    while True:
        engine_ui(f"USER PORTAL — {username.upper()}")
        menu = [
            ("1", "DEPOSIT WASTE", CYAN),
            ("2", "VIEW ROUTES", GREEN),
            ("3", "VIEW MY PENALTIES", ORANGE),
            ("0", "LOGOUT", RED)
        ]
        for key, label, clr in menu:
            print(f"   {SAFFRON}★{RESET} {clr}{key}.{RESET} {clr}{label}{RESET}")

        ch = input(f"\n {BOLD}{SAFFRON}ENTER OPTION > {RESET}")

        if ch == "0":
            session_logs.append(f"Logout: User {username} session ended"); break
        elif ch == "1": inject_waste(current_user=username)
        elif ch == "2": hub_mapping()
        elif ch == "3": show_user_penalties(username)

def show_user_penalties(username):
    engine_ui(f"PENALTY RECORD — {username.upper()}")
    penalties = user_penalties.get(username, [])

    if not penalties:
        print(f"\n {GREEN}✅ NO PENALTIES ON RECORD. KEEP IT UP!{RESET}")
        pause(); return

    total = sum(p["amount"] for p in penalties)
    print(f"\n {SAFFRON}{'#':<4} {'BIN':<8} {'WASTE TYPE':<18} {'PENALTY':<12} {'TIME'}{RESET}")
    print(f" {SAFFRON}{'='*65}{RESET}")
    for i, p in enumerate(penalties, 1):
        print(f" {WHITE}{i:<4}{RESET} {CYAN}{p['bin']:<8}{RESET} {YELLOW}{p['waste_type']:<18}{RESET} "
              f"{RED}₹{p['amount']:<11}{RESET} {PURPLE}{p['time']}{RESET}")
    print(f"\n {BOLD}{RED}TOTAL PENALTIES: ₹{total}{RESET}  |  {YELLOW}VIOLATIONS: {len(penalties)}{RESET}")
    pause()

# -------------------------------------------------------------------------
# ----------------------------- BIN OPERATIONS ----------------------------
# -------------------------------------------------------------------------

def inject_waste(current_user=None):
    global treasury_balance, daily_revenue, total_revenue

    engine_ui("INJECT WASTE PROTOCOL")
    print(f" {PURPLE}AVAILABLE LOCATIONS FOR INJECTION:{RESET}\n")
    print(f" {CYAN}{', '.join(sorted(area_to_bins.keys()))}{RESET}\n")

    area_input = input(f" {CYAN}ENTER TARGET AREA > {RESET}").strip().upper()
    matched_area = next((a for a in area_to_bins if a.upper() == area_input), None)

    if not matched_area:
        print(f"\n {RED}❌ FAILED: AREA NOT RECOGNIZED IN DATABASE{RESET}")
        time.sleep(1); return

    bins = area_to_bins[matched_area]

    if len(bins) > 1:
        print(f"\n {YELLOW}MULTIPLE UNITS DETECTED IN {matched_area.upper()}:{RESET}")
        for b_id in bins:
            print(f" {SAFFRON} └─ {b_id}{RESET} {GREEN}(Load: {bin_fill[b_id]}/{MAX_LIMIT}){RESET}")
        target_bin = input(f"\n {CYAN}SELECT SPECIFIC BIN ID > {RESET}").upper().strip()
        if target_bin not in bins:
            print(f"\n {RED}❌ FAILED: INVALID ID FOR THIS AREA{RESET}")
            time.sleep(1); return
    else:
        target_bin = bins[0]

    source = bin_data[target_bin]["source"]
    categories = allowed_waste[source]

    print(f"\n {YELLOW}{'='*150}{RESET}")
    print(f" {BOLD}{CYAN}BIN:{RESET} {GREEN}{target_bin}{RESET} | "
          f"{BOLD}{CYAN}SOURCE:{RESET} {WHITE}{source}{RESET}")
    print(f" {GREEN}ALLOWED TYPES:{RESET} {ORANGE}{', '.join(categories)}{RESET}")
    print(f" {YELLOW}{'='*150}{RESET}")

    wtype = input(f"\n {PURPLE}INPUT WASTE TYPE > {RESET}").upper().strip()
    try:
        qty = float(input(f" {PURPLE}QUANTITY IN KG > {RESET}"))
    except ValueError:
        print(f" {RED}Invalid numeric input.{RESET}"); return

    if qty <= 0:
        print(f" {RED}Quantity must be positive.{RESET}"); time.sleep(1); return

    if wtype not in categories:
        contaminated[target_bin] = True
        total_revenue += PENALTY
        daily_revenue += PENALTY
        treasury_balance += PENALTY

        if current_user:
            if current_user not in user_penalties:
                user_penalties[current_user] = []
            user_penalties[current_user].append({
                "bin": target_bin, "waste_type": wtype,
                "amount": PENALTY, "time": time.strftime("%H:%M:%S")
            })

        session_logs.append(f"CONTAMINATION: {target_bin} | {wtype} injected by {current_user or 'admin'}")
        show_alert(f"CONTAMINATION detected in {target_bin}! Penalty applied.", "WARNING", 8)

    bin_subtypes[target_bin][wtype] = bin_subtypes[target_bin].get(wtype, 0) + qty
    bin_last_updated[target_bin] = time.time()

    if bin_fill[target_bin] + qty > MAX_LIMIT:
        overflow[target_bin] += (bin_fill[target_bin] + qty - MAX_LIMIT)
        bin_fill[target_bin] = MAX_LIMIT
        session_logs.append(f"OVERFLOW: {target_bin} has exceeded capacity")
        show_alert(f"OVERFLOW alert: {target_bin} has exceeded capacity!", "CRITICAL", 10)
    else:
        bin_fill[target_bin] += qty

    save_all_state()
    print(f"\n {GREEN}✅ SUCCESSFUL INJECTION RECORDED{RESET}")
    time.sleep(1.5)

def show_bins():
    engine_ui("CITY BIN DASHBOARD")
    
    print(f"\n {SAFFRON}{'BIN':<6} {'AREA':<14} {'SOURCE':<12} {'PRIO':<5} {'FILL GAUGE':<22} {'LOAD':<10} {'OVF':<5} {'CONTAM':<7} {'STATUS':<10} {'VEHICLE':<8}{RESET}")
    print(f" {SAFFRON}{'='*115}{RESET}")

    for b in sorted(bin_data.keys()):
        area = bin_data[b]["area"]
        source = bin_data[b]["source"]
        prio_val = category_priority[source]
        prio_stars = f"{YELLOW}{'★' * prio_val}{'☆' * (5 - prio_val)}{RESET}"
        
        fill = bin_fill[b]
        fill_percent = int((fill / MAX_LIMIT) * 20)
        fill_bar = f"{GREEN}{'█' * fill_percent}{RED}{'░' * (20 - fill_percent)}{RESET}"
        
        load_text = f"{int(fill):>3}/{MAX_LIMIT:<3}"
        overflow_val = int(overflow[b])
        
        contam = "YES" if contaminated[b] else "NO"
        contam_color = RED if contaminated[b] else GREEN
        
        if overflow[b] > 0:
            status_text = "OVERFLOW"
            status_color = RED
        elif fill >= MAX_LIMIT:
            status_text = "FULL"
            status_color = YELLOW
        else:
            status_text = "OK"
            status_color = GREEN
        
        active_vehicle = area_active_vehicle[area] or "-"
        
        print(f" {CYAN}{b:<6}{RESET} "
              f"{WHITE}{area:<14}{RESET} "
              f"{PURPLE}{source:<12}{RESET} "
              f"{prio_stars:<5} "
              f"{fill_bar:<22} "
              f"{WHITE}{load_text:<10}{RESET} "
              f"{ORANGE}{overflow_val:<5}{RESET} "
              f"{contam_color}{contam:<7}{RESET} "
              f"{status_color}{status_text:<10}{RESET} "
              f"{CYAN}{active_vehicle:<8}{RESET}")

    total_fill = sum(bin_fill.values())
    total_overflow_sum = sum(overflow.values())
    bins_with_waste = len([b for b in bin_fill if bin_fill[b] > 0])
    
    print(f"\n{BOLD}{GREEN}📊 SUMMARY:{RESET}")
    print(f"   {CYAN}Total Waste: {total_fill:.1f} kg | Overflow: {total_overflow_sum:.1f} kg | Active Bins: {bins_with_waste}/{len(bin_data)}{RESET}")
    print(f"   {CYAN}Total Revenue: ₹{total_revenue} | Treasury: {GREEN if treasury_balance>=0 else RED}₹{treasury_balance:.2f}{RESET}")
    pause()

# -------------------------------------------------------------------------
# ----------------------------- MAINTENANCE MODULE ------------------------
# -------------------------------------------------------------------------

def fleet_management():
    global treasury_balance, daily_expense

    while True:
        engine_ui("FLEET LOGISTICS & MAINTENANCE")
        print(f" {SAFFRON}{'ID':<6} {'TYPE':<20} {'AREA':<14} {'FUEL':<10} {'HEALTH':<10} {'STATUS':<10} {'ROLE':<10}{RESET}")
        print(f" {SAFFRON}{'='*95}{RESET}")

        for b in sorted(vehicles):
            area = bin_data[b]["area"]
            vtype = get_vehicle_type(b)
            broken = "BROKEN" if vehicle_broken[b] else "OK"
            broken_color = RED if vehicle_broken[b] else GREEN
            f_clr = GREEN if vehicles[b] > 50 else (YELLOW if vehicles[b] > 20 else RED)
            h_clr = GREEN if vehicle_health[b] > 60 else (YELLOW if vehicle_health[b] > 30 else RED)
            
            role = "ACTIVE" if area_active_vehicle[area] == b else ("STANDBY" if b in area_vehicle_standby[area] else "IDLE")
            role_color = GREEN if role == "ACTIVE" else (BLUE if role == "STANDBY" else YELLOW)
            
            print(f" {WHITE}{b:<6}{RESET} {CYAN}{vtype:<20}{RESET} {area:<14} "
                  f"{f_clr}{vehicles[b]:<10.1f}%{RESET} {h_clr}{vehicle_health[b]:<10.1f}%{RESET} "
                  f"{broken_color}{broken:<10}{RESET} {role_color}{role:<10}{RESET}")

        print(f"\n {CYAN}[1] REFUEL ALL   [2] SERVICE FLEET   [3] REPAIR BROKEN   [4] VIEW AREA QUEUES   [5] VIEW DISPATCH TIMES   [0] BACK{RESET}")
        opt = input(f"\n {SAFFRON}SELECT OPTION > {RESET}")

        if opt == "0":
            break
        elif opt == "1":
            total_cost = sum((100 - vehicles[b]) * REFUEL_COST_PER_PERCENT for b in vehicles if vehicles[b] < 100)
            if total_cost > 0 and treasury_balance >= total_cost:
                for b in vehicles: vehicles[b] = 100.0
                treasury_balance -= total_cost
                daily_expense += total_cost
                session_logs.append(f"Fleet refueled. Cost Rs.{int(total_cost)}")
                print(f" {GREEN}Refueling complete. Cost: ₹{int(total_cost)}{RESET}")
            elif total_cost > 0:
                print(f" {RED}Insufficient funds! Need ₹{total_cost:.2f}{RESET}")
            else:
                print(f" {GREEN}All vehicles already at 100% fuel.{RESET}")
            save_all_state()
            treasury_check()
            time.sleep(1.5)
        elif opt == "2":
            total_cost = sum((100 - vehicle_health[b]) * SERVICE_COST_PER_PERCENT for b in vehicle_health if vehicle_health[b] < 100)
            if total_cost > 0 and treasury_balance >= total_cost:
                for b in vehicle_health: 
                    vehicle_health[b] = 100.0
                    vehicle_broken[b] = False
                treasury_balance -= total_cost
                daily_expense += total_cost
                session_logs.append(f"Fleet serviced. Cost Rs.{int(total_cost)}")
                print(f" {GREEN}Fleet serviced. Cost: ₹{int(total_cost)}{RESET}")
            elif total_cost > 0:
                print(f" {RED}Insufficient funds! Need ₹{total_cost:.2f}{RESET}")
            else:
                print(f" {GREEN}All vehicles already at 100% health.{RESET}")
            save_all_state()
            treasury_check()
            time.sleep(1.5)
        elif opt == "3":
            broken_vehicles = [b for b in vehicle_broken if vehicle_broken[b]]
            total_cost = len(broken_vehicles) * 250
            if total_cost > 0 and treasury_balance >= total_cost:
                for b in broken_vehicles:
                    vehicle_broken[b] = False
                    vehicle_health[b] = max(vehicle_health[b], 60)
                treasury_balance -= total_cost
                daily_expense += total_cost
                session_logs.append(f"Broken vehicles repaired. Cost Rs.{int(total_cost)}")
                print(f" {GREEN}Broken vehicles repaired. Cost: ₹{int(total_cost)}{RESET}")
            elif total_cost > 0:
                print(f" {RED}Insufficient funds! Need ₹{total_cost:.2f}{RESET}")
            else:
                print(f" {GREEN}No broken vehicles to repair.{RESET}")
            save_all_state()
            treasury_check()
            time.sleep(1.5)
        elif opt == "4":
            show_area_queues()
        elif opt == "5":
            show_dispatch_times()

def show_dispatch_times():
    """Show dispatch analysis with reroute information"""
    engine_ui("DISPATCH TIME ANALYSIS - WITH REROUTE INFO")
    
    if not dispatch_logs:
        print(f"\n {YELLOW}No dispatch records found. Perform some collections first.{RESET}")
        pause()
        return
    
    print(f"\n {SAFFRON}{'─'*140}{RESET}")
    print(f" {BOLD}{CYAN}📊 DISPATCH ANALYSIS WITH REROUTE DETAILS{RESET}")
    print(f" {SAFFRON}{'─'*140}{RESET}")
    
    # Header
    print(f"\n {BOLD}{'TIME':<8} {'BIN':<5} {'VEH':<5} {'ORIG AREA':<12} {'REROUTE FROM':<12} {'WASTE':<12} {'TRAFFIC':<8} {'BASE':<5} {'ACTUAL':<6} {'DIFF':<6} {'STATUS'}{RESET}")
    print(f" {SAFFRON}{'─'*140}{RESET}")
    
    total_base = 0
    total_actual = 0
    reroute_count = 0
    total_reroute_distance_saved = 0
    
    for log in dispatch_logs[-30:]:  # Show last 30 dispatches
        reroute_status = "✅ REROUTED" if log['rerouted'] else "❌ DIRECT"
        reroute_color = GREEN if log['rerouted'] else WHITE
        
        orig_area_display = log['original_area'][:10]
        reroute_from = log['rerouted_from_area'][:10] if log['rerouted_from_area'] else "-"
        
        # Calculate distance saved (original vs actual)
        if log['rerouted'] and log.get('original_distance', 0) > 0:
            dist_saved = log['original_distance'] - log['distance_km']
            total_reroute_distance_saved += dist_saved if dist_saved > 0 else 0
        
        print(f"{CYAN}{log['timestamp']:<8}{RESET} "
              f"{WHITE}{log['bin']:<5}{RESET} "
              f"{log['vehicle']:<5} "
              f"{orig_area_display:<12} "
              f"{YELLOW}{reroute_from:<12}{RESET} "
              f"{PURPLE}{log['waste_type']:<12}{RESET} "
              f"{MAGENTA}{log['traffic_level']:<8}{RESET} "
              f"{log['base_time_min']:<5} "
              f"{log['actual_time_min']:<6} "
              f"{RED if log['time_difference']>0 else GREEN}{log['time_difference']:<6}{RESET} "
              f"{reroute_color}{reroute_status}{RESET}")
    
    # Summary Statistics
    print(f"\n {BOLD}{CYAN}{'='*140}{RESET}")
    print(f" {BOLD}{CYAN}📈 DISPATCH STATISTICS SUMMARY:{RESET}")
    print(f" {SAFFRON}{'─'*70}{RESET}")
    
    total_dispatches = len(dispatch_logs)
    reroute_count = sum(1 for log in dispatch_logs if log['rerouted'])
    direct_count = total_dispatches - reroute_count
    
    avg_base = sum(log['base_time_min'] for log in dispatch_logs) / total_dispatches
    avg_actual = sum(log['actual_time_min'] for log in dispatch_logs) / total_dispatches
    avg_delay = avg_actual - avg_base
    
    print(f"\n {CYAN}📊 General Statistics:{RESET}")
    print(f"   Total Dispatches:     {total_dispatches}")
    print(f"   ✅ Rerouted:          {reroute_count} ({reroute_count/total_dispatches*100:.1f}%)")
    print(f"   ❌ Direct:            {direct_count} ({direct_count/total_dispatches*100:.1f}%)")
    print(f"   ⏱️ Average Base Time:  {avg_base:.1f} min")
    print(f"   ⏱️ Average Actual Time:{avg_actual:.1f} min")
    print(f"   📈 Average Delay:     {avg_delay:+.1f} min")
    
    # Reroute specific statistics
    if reroute_count > 0:
        reroute_logs = [log for log in dispatch_logs if log['rerouted']]
        avg_reroute_dist = sum(log.get('alternative_distance', 0) for log in reroute_logs) / reroute_count
        avg_original_dist = sum(log.get('original_distance', 0) for log in reroute_logs) / reroute_count
        
        print(f"\n {YELLOW}🔄 Reroute Statistics:{RESET}")
        print(f"   Average distance from alternative area to bin: {avg_reroute_dist:.1f} km")
        print(f"   Average original distance (bin to facility):   {avg_original_dist:.1f} km")
        print(f"   Total distance saved via rerouting:            {total_reroute_distance_saved:.1f} km")
        
        # Find most common reroute area
        reroute_areas = {}
        for log in reroute_logs:
            area = log.get('rerouted_from_area')
            if area:
                reroute_areas[area] = reroute_areas.get(area, 0) + 1
        
        if reroute_areas:
            most_common = max(reroute_areas, key=reroute_areas.get)
            print(f"   Most frequent reroute source area: {most_common} ({reroute_areas[most_common]} times)")
    
    # Traffic impact analysis
    print(f"\n {MAGENTA}🚦 Traffic Impact Analysis:{RESET}")
    traffic_levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "VERY HIGH": 0}
    for log in dispatch_logs:
        if log['traffic_level'] in traffic_levels:
            traffic_levels[log['traffic_level']] += 1
    
    for level, count in traffic_levels.items():
        if count > 0:
            pct = count / total_dispatches * 100
            level_color = GREEN if level == "LOW" else (YELLOW if level == "MEDIUM" else RED)
            print(f"   {level_color}{level:<10}{RESET}: {count:>3} dispatches ({pct:.1f}%)")
    
    pause()

def show_area_queues():
    engine_ui("AREA VEHICLE QUEUES")
    
    print(f"\n {YELLOW}━━━ AREA VEHICLE STATUS ━━━{RESET}\n")
    
    for area in sorted(area_to_bins.keys()):
        active = area_active_vehicle[area]
        standby = area_vehicle_standby[area]
        
        print(f" {CYAN}▶ {area}{RESET}")
        print(f"    {GREEN}Active: {active if active else 'None'}{RESET}")
        print(f"    {BLUE}Standby: {', '.join(standby) if standby else 'None'}{RESET}")
        print()
    
    pause()

# -------------------------------------------------------------------------
# ----------------------------- EXTERNAL CONDITIONS -----------------------
# -------------------------------------------------------------------------

def external_conditions_panel():
    global weather_mode

    while True:
        engine_ui("WEATHER & ENVIRONMENTAL CONDITIONS")
        cal_status, cal_name = get_calendar_status()

        print(f"\n {CYAN}CALENDAR:{RESET} {YELLOW}{cal_status} - {cal_name}{RESET}")
        print(f" {CYAN}WEATHER MODE:{RESET} {YELLOW}{weather_mode}{RESET}")
        print(f" {CYAN}WINDY API:{RESET} {'✅ AVAILABLE' if WINDY_API_KEY else '❌ NOT SET'}")
        print(f" {CYAN}CALENDARIFIC API:{RESET} {'✅ AVAILABLE' if CALENDARIFIC_API_KEY else '❌ NOT SET (Weekend-only mode active)'}\n")

        print(f" {SAFFRON}{'AREA':<16} {'WEATHER':<12} {'RAIN':<6} {'WIND':<8} {'TEMP':<6} {'TRAFFIC':<12} {'ROAD':<8}{RESET}")
        print(f" {SAFFRON}{'='*75}{RESET}")

        for area in sorted(coordinates):
            risk, weather = weather_risk_score(area)
            traffic = get_traffic_level(area)
            road = "CLOSED" if area in road_closures else "OPEN"
            road_color = RED if road == "CLOSED" else GREEN
            traffic_color = RED if traffic in ["VERY HIGH", "HIGH"] else (YELLOW if traffic == "MEDIUM" else GREEN)
            
            print(f"{WHITE}{area:<16}{RESET} "
                  f"{PURPLE}{weather['condition']:<12}{RESET} "
                  f"{BLUE}{weather['rain_mm']:<6}{RESET} "
                  f"{BLUE}{weather['wind_kmph']:<8}{RESET} "
                  f"{ORANGE}{weather['temperature']:<6}{RESET} "
                  f"{traffic_color}{traffic:<12}{RESET} "
                  f"{road_color}{road:<8}{RESET}")

        print(f"\n {CYAN}[1] UPDATE MANUAL WEATHER{RESET}")
        print(f" {CYAN}[2] SET TRAFFIC OVERRIDE{RESET}")
        print(f" {CYAN}[3] CLEAR TRAFFIC OVERRIDE{RESET}")
        print(f" {CYAN}[4] TOGGLE ROAD CLOSURE{RESET}")
        print(f" {CYAN}[5] TOGGLE FACILITY STATUS{RESET}")
        print(f" {CYAN}[6] SHOW HOLIDAY CACHE{RESET}")
        print(f" {CYAN}[7] SWITCH WEATHER MODE{RESET}")
        print(f" {CYAN}[8] VIEW PROCESSING FACILITIES{RESET}")
        print(f" {RED}[0] BACK{RESET}")

        ch = input(f"\n {SAFFRON}SELECT OPTION > {RESET}")

        if ch == "0":
            break
        elif ch == "1":
            area = input("Area: ").strip().upper()
            matched = next((a for a in coordinates if a.upper() == area), None)
            if not matched:
                print(f"{RED}Invalid area.{RESET}"); time.sleep(1); continue
            condition = input("Condition CLEAR/LIGHT_RAIN/HEAVY_RAIN/STORM/EXTREME_HEAT: ").strip().upper()
            try:
                rain = float(input("Rain mm: ") or 0)
                wind = float(input("Wind kmph: ") or 0)
                temp = float(input("Temperature C: ") or 31)
            except ValueError:
                print(f"{RED}Invalid numeric input.{RESET}"); time.sleep(1); continue
            manual_weather[matched] = {"condition": condition, "rain_mm": rain, "wind_kmph": wind, "temperature": temp}
            session_logs.append(f"Manual weather updated for {matched}")
            print(f"{GREEN}Manual weather updated.{RESET}"); time.sleep(1)
        elif ch == "2":
            area = input("Area: ").strip().upper()
            matched = next((a for a in coordinates if a.upper() == area), None)
            if not matched:
                print(f"{RED}Invalid area.{RESET}"); time.sleep(1); continue
            level = input("Traffic LOW/MEDIUM/HIGH/VERY HIGH/BLOCKED: ").strip().upper()
            if level not in ["LOW", "MEDIUM", "HIGH", "VERY HIGH", "BLOCKED"]:
                print(f"{RED}Invalid traffic level.{RESET}"); time.sleep(1); continue
            traffic_overrides[matched] = level
            if level in ["VERY HIGH", "BLOCKED"]:
                show_alert(f"Traffic {level} detected in {matched}. Rerouting may be triggered.", "WARNING", 10)
            print(f"{GREEN}Traffic override set.{RESET}"); time.sleep(1)
        elif ch == "3":
            area = input("Area to clear override: ").strip().upper()
            matched = next((a for a in traffic_overrides if a.upper() == area), None)
            if matched:
                del traffic_overrides[matched]
                print(f"{GREEN}Traffic override cleared.{RESET}")
            else:
                print(f"{YELLOW}No override found.{RESET}")
            time.sleep(1)
        elif ch == "4":
            area = input("Area: ").strip().upper()
            matched = next((a for a in coordinates if a.upper() == area), None)
            if not matched:
                print(f"{RED}Invalid area.{RESET}"); time.sleep(1); continue
            if matched in road_closures:
                road_closures.remove(matched)
                print(f"{GREEN}Road reopened.{RESET}")
            else:
                road_closures.add(matched)
                show_alert(f"ROAD CLOSURE reported in {matched}. Automatic rerouting initiated.", "CRITICAL", 10)
                print(f"{RED}Road closed.{RESET}")
            time.sleep(1)
        elif ch == "5":
            print("\nProcessing Facilities:")
            for f_name, f_data in processing_facilities.items():
                status_color = GREEN if f_data['status'] == 'OPEN' else RED
                print(f"  {f_name:<35} {status_color}{f_data['status']}{RESET} ({', '.join(f_data['waste_types'])})")
            facility = input("\nFacility name: ").strip().upper()
            matched_facility = None
            for f_name in processing_facilities.keys():
                if facility in f_name.upper():
                    matched_facility = f_name
                    break
            if not matched_facility:
                print(f"{RED}Invalid facility.{RESET}"); time.sleep(1); continue
            processing_facilities[matched_facility]["status"] = "CLOSED" if processing_facilities[matched_facility]["status"] == "OPEN" else "OPEN"
            save_all_state()
            print(f"{GREEN}Facility status updated.{RESET}"); time.sleep(1)
        elif ch == "6":
            year = time.localtime().tm_year
            holidays = fetch_indian_holidays(year)
            print(f"\nIndian public holidays for {year}:")
            if not holidays:
                print("No holiday data loaded. Weekend-only mode active.")
            else:
                for d, info in holidays.items():
                    print(f"  {d} - {info['name']}")
            pause()
        elif ch == "7":
            if weather_mode == "MANUAL":
                weather_mode = "WINDY"
                print(f"{GREEN}Weather mode switched to WINDY. Dynamic rerouting ENABLED.{RESET}")
            else:
                weather_mode = "MANUAL"
                print(f"{GREEN}Weather mode switched to MANUAL. Using static routes only.{RESET}")
            time.sleep(1.5)
        elif ch == "8":
            show_processing_facilities()

# -------------------------------------------------------------------------
# ----------------------------- VEHICLE STATUS DASHBOARD ------------------
# -------------------------------------------------------------------------

def vehicle_status_dashboard():
    global treasury_balance, daily_expense

    while True:
        engine_ui("VEHICLE STATUS DASHBOARD")
        print(f"{CYAN}REAL-TIME VEHICLE MONITORING{RESET}\n")
        print(f"{SAFFRON}{'ID':<6} {'AREA':<14} {'TYPE':<16} {'FUEL':<8} {'HEALTH':<8} {'TRAFFIC':<10} {'WEATHER':<10} {'STATUS':<12}{RESET}")
        print(f"{SAFFRON}{'='*100}{RESET}")

        for b in sorted(bin_data):
            area = bin_data[b]["area"]
            vtype = get_vehicle_type(b)
            traffic = get_traffic_level(area)
            risk, weather = weather_risk_score(area)
            f_clr = GREEN if vehicles[b] > 50 else (YELLOW if vehicles[b] > 20 else RED)
            h_clr = GREEN if vehicle_health[b] > 60 else (YELLOW if vehicle_health[b] > 30 else RED)
            
            if vehicle_broken[b]:
                status = "BROKEN"
                status_color = RED
            elif area_active_vehicle[area] == b:
                status = "ACTIVE"
                status_color = GREEN
            elif b in area_vehicle_standby[area]:
                status = "STANDBY"
                status_color = BLUE
            else:
                status = "IDLE"
                status_color = YELLOW
            
            print(f"{WHITE}{b:<6}{RESET} {CYAN}{area:<14}{RESET} {PURPLE}{vtype:<16}{RESET} "
                  f"{f_clr}{vehicles[b]:<8.1f}{RESET} {h_clr}{vehicle_health[b]:<8.1f}{RESET} "
                  f"{MAGENTA}{traffic:<10}{RESET} {BLUE}{weather['condition']:<10}{RESET} "
                  f"{status_color}{status:<12}{RESET}")

        print(f"\n{CYAN}[1] REFUEL ALL   [2] SERVICE FLEET   [3] REPAIR BROKEN   [4] SHOW AREA QUEUES   [5] SHOW DISPATCH TIMES   [0] BACK{RESET}")
        ch = input(f"\n{SAFFRON}SELECT OPTION > {RESET}")

        if ch == "0": break
        elif ch == "1":
            total_cost = sum((100 - vehicles[b]) * REFUEL_COST_PER_PERCENT for b in vehicles if vehicles[b] < 100)
            if total_cost > 0 and treasury_balance >= total_cost:
                for b in vehicles: vehicles[b] = 100.0
                treasury_balance -= total_cost
                daily_expense += total_cost
                print(f"{GREEN}All vehicles refueled. Cost: ₹{int(total_cost)}{RESET}")
            elif total_cost > 0:
                print(f"{RED}Insufficient funds! Need ₹{total_cost:.2f}{RESET}")
            else:
                print(f"{GREEN}All vehicles already at 100% fuel.{RESET}")
            save_all_state()
            time.sleep(1.5)
        elif ch == "2":
            total_cost = sum((100 - vehicle_health[b]) * SERVICE_COST_PER_PERCENT for b in vehicle_health if vehicle_health[b] < 100)
            if total_cost > 0 and treasury_balance >= total_cost:
                for b in vehicle_health: 
                    vehicle_health[b] = 100.0
                    vehicle_broken[b] = False
                treasury_balance -= total_cost
                daily_expense += total_cost
                print(f"{GREEN}Fleet serviced. Cost: ₹{int(total_cost)}{RESET}")
            elif total_cost > 0:
                print(f"{RED}Insufficient funds! Need ₹{total_cost:.2f}{RESET}")
            else:
                print(f"{GREEN}All vehicles already at 100% health.{RESET}")
            save_all_state()
            time.sleep(1.5)
        elif ch == "3":
            broken_vehicles = [b for b in vehicle_broken if vehicle_broken[b]]
            total_cost = len(broken_vehicles) * 250
            if total_cost > 0 and treasury_balance >= total_cost:
                for b in broken_vehicles:
                    vehicle_broken[b] = False
                    vehicle_health[b] = max(vehicle_health[b], 60)
                treasury_balance -= total_cost
                daily_expense += total_cost
                print(f"{GREEN}Broken vehicles repaired. Cost: ₹{int(total_cost)}{RESET}")
            elif total_cost > 0:
                print(f"{RED}Insufficient funds! Need ₹{total_cost:.2f}{RESET}")
            else:
                print(f"{GREEN}No broken vehicles to repair.{RESET}")
            save_all_state()
            time.sleep(1.5)
        elif ch == "4":
            show_area_queues()
        elif ch == "5":
            show_dispatch_times()

# -------------------------------------------------------------------------
# ----------------------------- DISPATCH OPERATIONS -----------------------
# -------------------------------------------------------------------------

def priority_clear():
    filled = [b for b in bin_data if bin_fill[b] > 0 or overflow[b] > 0]

    if not filled:
        print(f"\n {YELLOW}⚠️ ALL BINS ARE EMPTY. NO DISPATCH REQUIRED.{RESET}")
        time.sleep(1.5); return

    overflow_bins = [b for b in filled if overflow[b] > 0]
    critical_bins = [b for b in filled if overflow[b] == 0 and bin_fill[b] >= MAX_LIMIT * 0.9]
    normal_bins = [b for b in filled if overflow[b] == 0 and bin_fill[b] < MAX_LIMIT * 0.9]

    if overflow_bins:
        target = max(overflow_bins, key=lambda x: (category_priority[bin_data[x]["source"]], overflow[x]))
    elif critical_bins:
        target = max(critical_bins, key=lambda x: (category_priority[bin_data[x]["source"]], bin_fill[x]))
    else:
        target = max(normal_bins, key=lambda x: (category_priority[bin_data[x]["source"]], bin_fill[x]))

    area = bin_data[target]["area"]
    
    area_bins = [b for b in area_to_bins[area] if bin_fill[b] > 0 or overflow[b] > 0]
    if len(area_bins) > 1:
        optimize_route_for_zone(area)
    
    traffic = get_traffic_level(area)
    force_reroute = (traffic in ["VERY HIGH", "BLOCKED"] or area in road_closures)
    
    if force_reroute:
        print(f" {YELLOW}🔄 Traffic/weather alerts active. Using dynamic routing...{RESET}")

    success = reduce_fuel(target, force_reroute=force_reroute)

    if success:
        print(f" {GREEN}✅ UNIT {target} CLEARED SUCCESSFULLY{RESET}")

    time.sleep(1.5)

def manual_zone_clearance():
    engine_ui("MANUAL ZONE CLEARANCE")
    print(f" {PURPLE}REGISTERED AREAS:{RESET} {CYAN}{', '.join(sorted(area_to_bins.keys()))}{RESET}\n")
    print(f" {YELLOW}━━━ MANUAL DISPATCH MODE ━━━{RESET}")
    print(f" {WHITE}Select an area to clear all its bins using the ACTIVE vehicle{RESET}\n")
    
    area_input = input(f" {CYAN}ZONE TO CLEAR > {RESET}").strip()
    matched = next((a for a in area_to_bins if a.lower() == area_input.lower()), None)

    if not matched:
        print(f" {RED}❌ ERROR: AREA NOT RECOGNIZED{RESET}"); time.sleep(1); return

    optimize_route_for_zone(matched)

    print(f"\n {YELLOW}BINS DETECTED IN {matched.upper()}:{RESET}")
    for b in area_to_bins[matched]:
        fill_pct = (bin_fill[b] / MAX_LIMIT) * 100
        status = "OVERFLOW" if overflow[b] > 0 else ("FULL" if bin_fill[b] >= MAX_LIMIT else f"{fill_pct:.0f}%")
        print(f"  {CYAN}• {b}{RESET} (Load: {bin_fill[b]}/{MAX_LIMIT} - {status})")

    print(f"\n {CYAN}[1] CLEAR ALL BINS IN THIS ZONE (Using ACTIVE vehicle){RESET}")
    print(f" {CYAN}[2] CLEAR ALL BINS WITH REROUTING{RESET}")
    print(f" {CYAN}[3] CLEAR SPECIFIC BIN{RESET}")
    print(f" {RED}[0] CANCEL{RESET}")
    
    mode = input(f"\n {SAFFRON}SELECT MODE > {RESET}").strip()
    
    if mode == "0":
        return
    
    if mode == "3":
        b_in = input(f" {CYAN}ENTER BIN ID: {RESET}").upper().strip()
        if b_in in area_to_bins[matched]:
            force = input(f" {YELLOW}Enable rerouting? (y/n): {RESET}").lower() == 'y'
            if reduce_fuel(b_in, force_reroute=force):
                print(f" {GREEN}✅ {b_in} CLEARED{RESET}")
            else:
                print(f" {RED}❌ DISPATCH FAILED{RESET}")
        else:
            print(f" {RED}Invalid bin ID{RESET}")
    else:
        force = (mode == "2")
        collected = collect_all_bins_in_area(matched, force_reroute=force)
        print(f" {GREEN}✅ Zone clearance complete! {collected} bins cleared.{RESET}")
    
    time.sleep(1.5)

def full_city_sweep():
    engine_ui("FULL CITY SWEEP")
    print(f" {CYAN}INITIATING FULL CITY COLLECTION SWEEP...{RESET}\n")
    
    force = input(f" {YELLOW}Enable dynamic rerouting for this sweep? (y/n): {RESET}").lower() == 'y'
    
    total_cleared = 0
    for area in sorted(area_to_bins.keys()):
        optimize_route_for_zone(area)
        
        print(f"\n {BLUE}━━━ Processing Area: {area} ━━━{RESET}")
        cleared = collect_all_bins_in_area(area, force_reroute=force)
        total_cleared += cleared

    if total_cleared == 0:
        print(f"\n {YELLOW}⚠️ ALL CITY BINS ARE ALREADY EMPTY.{RESET}")
    else:
        print(f"\n {GREEN}✅ CITY SWEEP COMPLETE. {total_cleared} BINS PROCESSED.{RESET}")
    time.sleep(1.5)

def force_reroute_all_pending():
    engine_ui("FORCE REROUTE ALL PENDING")
    print(f"{YELLOW}🔄 FORCING DYNAMIC REROUTING FOR ALL PENDING BINS{RESET}\n")
    
    filled_areas = []
    for area in area_to_bins.keys():
        area_bins = [b for b in area_to_bins[area] if bin_fill[b] > 0 or overflow[b] > 0]
        if area_bins:
            filled_areas.append((area, len(area_bins)))
    
    if not filled_areas:
        print(f"{GREEN}No pending bins to reroute.{RESET}")
        pause()
        return
    
    print(f"{CYAN}Found bins in {len(filled_areas)} areas:{RESET}")
    for area, count in filled_areas:
        print(f"   {YELLOW}{area}: {count} bins{RESET}")
    
    print(f"\n{YELLOW}Rerouting will collect ALL bins in each area using active vehicles{RESET}\n")
    
    total_cleared = 0
    for area, _ in filled_areas:
        optimize_route_for_zone(area)
        
        print(f"\n {BLUE}Processing {area}...{RESET}")
        cleared = collect_all_bins_in_area(area, force_reroute=True)
        total_cleared += cleared
    
    print(f"\n{GREEN}Force reroute complete. {total_cleared} bins cleared.{RESET}")
    session_logs.append(f"Force reroute executed: {total_cleared} bins")
    pause()

# -------------------------------------------------------------------------
# ----------------------------- ANALYTICS & REPORTS -----------------------
# -------------------------------------------------------------------------

def generate_report():
    engine_ui("SYSTEM PERFORMANCE REPORT")
    total_load = sum(bin_fill.values())
    total_overflow = sum(overflow.values())
    active_bins = len([b for b in bin_fill if bin_fill[b] > 0])

    total_trips = len(dispatch_logs)
    total_reroutes = sum(1 for log in dispatch_logs if log['rerouted']) if dispatch_logs else 0
    
    total_fuel_cost = sum(log['cost'] for log in dispatch_logs) if dispatch_logs else 0

    total_facility_capacity = sum(f["capacity"] for f in processing_facilities.values())
    total_facility_load = sum(f["current_load"] for f in processing_facilities.values())
    total_temp_storage = sum(temporary_storage.values())

    print(f"\n {BOLD}{GREEN}{'='*60}{RESET}")
    print(f" {BOLD}{GREEN}🎯 SYSTEM GOALS & ACHIEVEMENTS{RESET}")
    print(f" {BOLD}{GREEN}{'='*60}{RESET}")
    
    print(f"\n {BOLD}1. IMPROVE WASTE SEGREGATION EFFICIENCY:{RESET}")
    contamination_count = sum(1 for b in contaminated if contaminated[b])
    print(f"   ✅ Waste correctly classified to appropriate facilities")
    print(f"   ⚠️ Contamination detected: {contamination_count} bins")
    
    print(f"\n {BOLD}2. OPTIMIZE COLLECTION AND PROCESSING OPERATIONS:{RESET}")
    print(f"   ✅ Collections performed: {total_trips}")
    print(f"   ✅ Rerouted collections: {total_reroutes}")
    print(f"   ✅ Active bins: {active_bins}/{len(bin_data)}")
    
    print(f"\n {BOLD}3. ENSURE ENVIRONMENTAL SUSTAINABILITY:{RESET}")
    print(f"   ✅ Waste routed to appropriate recycling facilities")
    print(f"   ✅ Contaminated waste sent to secondary segregation")
    print(f"   🌍 Total Emissions: {total_emissions:.2f} kg CO2")
    print(f"   ♻️ Recycled Waste: {total_recycled:.1f} kg")
    print(f"   🗑️ Landfill Waste: {total_landfill:.1f} kg")
    
    print(f"\n {BOLD}4. MINIMIZE OPERATIONAL COSTS:{RESET}")
    print(f"   💰 Total Fuel Cost: ₹{total_fuel_cost:.2f}")
    print(f"   🏭 Processing Cost: ₹{daily_processing_cost:.2f}")

    print(f"\n {BOLD}📊 FINANCIAL OVERVIEW{RESET}")
    print(f" {SAFFRON}{'='*50}{RESET}")
    print(f" {CYAN}Treasury Balance:      {GREEN if treasury_balance>=0 else RED}₹{treasury_balance:.2f}{RESET}")
    print(f" {CYAN}Revenue Collected:     {GREEN}₹{daily_revenue:.2f}{RESET}")
    print(f" {CYAN}Total Expenses:        {RED}₹{daily_expense:.2f}{RESET}")
    print(f" {CYAN}Net Profit:            {GREEN if (daily_revenue - daily_expense)>=0 else RED}₹{(daily_revenue - daily_expense):.2f}{RESET}")
    print(f" {CYAN}Total Waste Collected: {WHITE}{total_waste_collected:.1f} kg{RESET}")
    print(f" {CYAN}Total Load:            {WHITE}{total_load:.2f} kg{RESET}")
    print(f" {CYAN}Total Overflow:        {ORANGE}{total_overflow:.2f} kg{RESET}")

    print(f"\n {BOLD}🏭 FACILITY STATUS{RESET}")
    print(f" {SAFFRON}{'='*50}{RESET}")
    print(f" {CYAN}Total Facility Capacity: {WHITE}{total_facility_capacity:>8,} kg{RESET}")
    print(f" {CYAN}Current Facility Load:   {WHITE}{total_facility_load:>8,.0f} kg ({total_facility_load/total_facility_capacity*100:.1f}%){RESET}")
    print(f" {CYAN}Temporary Storage:       {WHITE}{total_temp_storage:>8} kg{RESET}")

    print(f"\n {BOLD}🚛 FLEET STATUS{RESET}")
    print(f" {SAFFRON}{'='*50}{RESET}")
    active_count = sum(1 for area, v in area_active_vehicle.items() if v is not None)
    standby_count = sum(len(standby) for standby in area_vehicle_standby.values())
    broken_count = sum(1 for v in vehicle_broken if vehicle_broken[v])
    
    print(f" {CYAN}Active Vehicles:       {GREEN}{active_count}{RESET}")
    print(f" {CYAN}Standby Vehicles:      {BLUE}{standby_count}{RESET}")
    print(f" {CYAN}Broken/Maintenance:    {RED}{broken_count}{RESET}")
    
    avg_fuel = sum(vehicles.values()) / len(vehicles)
    avg_health = sum(vehicle_health.values()) / len(vehicle_health)
    print(f" {CYAN}Average Fuel:          {YELLOW}{avg_fuel:.1f}%{RESET}")
    print(f" {CYAN}Average Health:        {YELLOW}{avg_health:.1f}%{RESET}")

    print(f"\n {BOLD}🌤️ SYSTEM STATUS{RESET}")
    print(f" {SAFFRON}{'='*50}{RESET}")
    print(f" {CYAN}Weather Mode:          {YELLOW}{weather_mode}{RESET}")
    print(f" {CYAN}Road Closures:         {RED if road_closures else GREEN}{len(road_closures)} areas{RESET}")
    print(f" {CYAN}Calendar Mode:         {YELLOW}{'API Active' if CALENDARIFIC_API_KEY else 'Weekend-only'}{RESET}")
    print(f" {CYAN}System Version:        {WHITE}{SYSTEM_VERSION}{RESET}")

    print(f"\n {BOLD}📋 RECENT LOGS{RESET}")
    for log in session_logs[-8:]:
        print(f" {MAGENTA}› {log}{RESET}")
    
    if alert_logs:
        print(f"\n {BOLD}⚠️ RECENT ALERTS{RESET}")
        for alert in alert_logs[-5:]:
            print(f" {RED}› {alert}{RESET}")
    
    pause()

def hub_mapping():
    engine_ui("HUB MAP & LOGISTICS")
    print(f"\n {CYAN}NETWORK STATUS: OSRM CLOUD INTERFACE ACTIVE{RESET}\n")
    print(f" {SAFFRON}{'BIN':<6} {'AREA':<16} {'DESTINATION':<15} {'KM':<8} {'MINS'}{RESET}")
    print(f" {SAFFRON}{'='*65}{RESET}")

    for b in sorted(bin_data.keys()):
        area = bin_data[b]["area"]
        source = bin_data[b]["source"]
        waste_cat = allowed_waste[source][0]
        km, mins = get_route_distance(coordinates[area], destinations[waste_cat])
        print(f" {CYAN}{b:<6}{RESET} {WHITE}{area:<16}{RESET} {GREEN}{waste_cat:<15}{RESET} {YELLOW}{km:<8}{RESET} {PURPLE}{mins}{RESET}")

    print(f"\n {CYAN}SAMPLE OPTIMIZED ROUTE PREVIEW{RESET}")
    sample_bins = get_priority_bins(5)
    if sample_bins:
        coords = [DEPOT] + build_route_for_bins(sample_bins) + [DEPOT]
        dist_km, mins, _ = get_optimized_trip(coords)
        print(f" {GREEN}Bins:{RESET} {sample_bins}")
        print(f" {YELLOW}Distance:{RESET} {dist_km} km | {PURPLE}Time:{RESET} {mins} mins")
    pause()

def add_admin():
    engine_ui("ADD NEW ADMIN")
    print(f"\n {CYAN}REGISTER A NEW ADMINISTRATOR{RESET}\n")

    username = input(f" {CYAN}NEW ADMIN USERNAME : {RESET}").strip()
    if not username:
        print(f" {RED}❌ USERNAME CANNOT BE EMPTY.{RESET}"); time.sleep(1); return
    if username in admins:
        print(f" {RED}❌ ADMIN ALREADY EXISTS.{RESET}"); time.sleep(1); return
    if username in users:
        print(f" {RED}❌ USERNAME ALREADY TAKEN BY A USER.{RESET}"); time.sleep(1); return

    password = input(f" {CYAN}SET PASSKEY        : {RESET}").strip()
    if not password:
        print(f" {RED}❌ PASSKEY CANNOT BE EMPTY.{RESET}"); time.sleep(1); return
    confirm = input(f" {CYAN}CONFIRM PASSKEY    : {RESET}").strip()
    if password != confirm:
        print(f" {RED}❌ PASSKEYS DO NOT MATCH.{RESET}"); time.sleep(1); return

    role = input(f" {CYAN}ROLE/DESIGNATION   : {RESET}").strip() or "Administrator"
    admins[username] = password
    save_all_state()
    session_logs.append(f"New admin registered: {username} ({role})")
    print(f"\n {GREEN}✅ ADMIN {username.upper()} REGISTERED SUCCESSFULLY!{RESET}")
    time.sleep(1.5)

# -------------------------------------------------------------------------
# ----------------------------- BACKGROUND TASKS --------------------------
# -------------------------------------------------------------------------

def background_processing():
    """Run background tasks like facility processing and random events"""
    process_facility_loads()
    update_facility_failures()
    random_facility_shutdown()
    save_all_state()

def clear_processing_plants():
    engine_ui("CLEAR PROCESSING PLANTS")
    print(f"\n {YELLOW}WARNING: This will reset the current load and temporary storage for processing facilities.{RESET}")
    print(f" {CYAN}[1] CLEAR ALL FACILITIES{RESET}")
    print(f" {CYAN}[2] CLEAR SPECIFIC FACILITY{RESET}")
    print(f" {RED}[0] CANCEL{RESET}")
    
    ch = input(f"\n {SAFFRON}SELECT OPTION > {RESET}").strip()
    
    if ch == "1":
        for f in processing_facilities:
            processing_facilities[f]["current_load"] = 0
            temporary_storage[f] = 0
        save_all_state()
        print(f" {GREEN}✅ ALL PROCESSING FACILITIES CLEARED.{RESET}")
        session_logs.append("Admin cleared all processing facilities.")
        time.sleep(1.5)
    elif ch == "2":
        print(f"\n {PURPLE}AVAILABLE FACILITIES:{RESET}")
        for f_name in processing_facilities.keys():
            print(f"  {CYAN}{f_name.replace('_', ' ')}{RESET}")
        facility = input(f"\n {CYAN}ENTER FACILITY NAME: {RESET}").strip().upper().replace(' ', '_')
        matched_facility = next((f for f in processing_facilities if facility and facility in f.upper()), None)
        if matched_facility:
            processing_facilities[matched_facility]["current_load"] = 0
            temporary_storage[matched_facility] = 0
            save_all_state()
            print(f" {GREEN}✅ {matched_facility.replace('_', ' ')} CLEARED.{RESET}")
            session_logs.append(f"Admin cleared facility: {matched_facility}")
        else:
            print(f" {RED}❌ INVALID FACILITY.{RESET}")
        time.sleep(1.5)

# -------------------------------------------------------------------------
# ----------------------------- ADMIN COMMAND CENTER ----------------------
# -------------------------------------------------------------------------

def admin_panel():
    while True:
        engine_ui("ADMIN COMMAND CENTER")
        menu = [
            ("1",  "INJECT WASTE RECORD",              CYAN),
            ("2",  "VIEW LIVE BIN MONITOR",             CYAN),
            ("3",  "PRIORITY CLEAR (SINGLE BIN)",       YELLOW),
            ("4",  "MANUAL ZONE CLEARANCE",             BLUE),
            ("5",  "FULL CITY SWEEP ROUTINE",           GREEN),
            ("6",  "FLEET & FUEL LOGISTICS",            SAFFRON),
            ("7",  "HUB MAPPING & DISTANCE",            PURPLE),
            ("8",  "GENERATION PERFORMANCE REPORT",     MAGENTA),
            ("9",  "CLEAR SECURITY LOGS",               RED),
            ("10", "ADD NEW ADMIN",                     ORANGE),
            ("11", "WEATHER CONDITIONS CHECK",          CYAN),
            ("12", "VEHICLE STATUS DASHBOARD",          MAGENTA),
            ("13", "FORCE REROUTE ALL PENDING",         YELLOW),
            ("14", "VIEW DISPATCH TIME ANALYSIS",       CYAN),
            ("15", "VIEW PROCESSING FACILITIES",        GREEN),
            ("16", "CLEAR PROCESSING PLANTS",           RED),
            ("0",  "LOGOUT AND LOCK SYSTEM",            WHITE)
        ]
        for key, label, clr in menu:
            print(f"   {SAFFRON}★{RESET} {clr}{key:2}.{RESET} {clr}{label}{RESET}")

        ch = input(f"\n {BOLD}{SAFFRON}ENTER COMMAND > {RESET}")

        if ch == "0":
            session_logs.append("Logout: Admin session ended"); break
        elif ch == "1":  inject_waste()
        elif ch == "2":  show_bins()
        elif ch == "3":  priority_clear()
        elif ch == "4":  manual_zone_clearance()
        elif ch == "5":  full_city_sweep()
        elif ch == "6":  fleet_management()
        elif ch == "7":  hub_mapping()
        elif ch == "8":  generate_report()
        elif ch == "9":
            session_logs.clear()
            alert_logs.clear()
            dispatch_logs.clear()
            print(f" {RED}All logs and alerts wiped from memory.{RESET}"); time.sleep(1)
        elif ch == "10": add_admin()
        elif ch == "11": external_conditions_panel()
        elif ch == "12": vehicle_status_dashboard()
        elif ch == "13": force_reroute_all_pending()
        elif ch == "14": show_dispatch_times()
        elif ch == "15": show_processing_facilities()
        elif ch == "16": clear_processing_plants()

# -------------------------------------------------------------------------
# ----------------------------- ENTRY POINT -------------------------------
# -------------------------------------------------------------------------

def start():
    engine_ui("INITIALIZING PRAAN CORE...")
    for msg in [
        "✓ Checking hardware sensors...",
        "✓ Loading area maps...",
        "✓ Establishing secure OSRM link...",
        "✓ Connecting weather services...",
        "✓ Initializing fleet management (One vehicle per area)...",
        "✓ Initializing processing facilities...",
        "✓ Verifying credentials database..."
    ]:
        print(f"  {GREEN}{msg}{RESET}")
        time.sleep(0.4)
    
    if CALENDARIFIC_API_KEY:
        print(f"  {GREEN}✓ Calendar API: Active (Indian holidays will be fetched){RESET}")
    else:
        print(f"  {YELLOW}⚠️ Calendar API: Not configured (Using weekend-only mode){RESET}")
    
    print(f"\n  {CYAN}📌 SYSTEM READY{RESET}")
    print(f"  {CYAN}📌 ONE ACTIVE VEHICLE PER AREA MODE ACTIVE{RESET}")
    print(f"  {CYAN}📌 Dynamic rerouting: {'ENABLED' if weather_mode == 'WINDY' else 'MANUAL'}{RESET}")
    print(f"  {CYAN}📌 Route Optimization: ENABLED (Multi-bin trips optimized){RESET}")
    print(f"  {CYAN}📌 Dispatch Time Tracking: ACTIVE (Shows reroute info){RESET}")
    print(f"  {CYAN}📌 Processing Facilities: {len(processing_facilities)} active{RESET}")
    print(f"  {CYAN}📌 Initial Treasury: ₹{treasury_balance:.2f}{RESET}")
    time.sleep(2)

    while True:
        background_processing()
        
        engine_ui("SYSTEM LOGIN")
        print(f"\n  {GREEN}[1] ADMIN PORTAL{RESET}")
        print(f"  {CYAN}[2] USER PORTAL — LOGIN{RESET}")
        print(f"  {YELLOW}[3] USER PORTAL — REGISTER{RESET}")
        print(f"  {RED}[4] TERMINATE SYSTEM{RESET}")

        choice = input(f"\n  {BOLD}{CYAN}PLEASE SELECT > {RESET}")

        if choice == "4":
            show_jaihind(); break

        if choice == "1":
            attempts = 3
            while attempts > 0:
                engine_ui("SECURE ADMIN AUTHENTICATION", hearts=attempts)
                u = input(f"  {CYAN}USERNAME: {RESET}").strip()
                p = input(f"  {CYAN}PASSKEY:  {RESET}").strip()

                if admins.get(u) == p:
                    session_logs.append(f"Access granted: {u}")
                    proceed = display_admin_profile(u)
                    if proceed:
                        admin_panel()
                    break

                attempts -= 1
                session_logs.append(f"Failed login attempt: {u}")
                print(f"  {RED}❌ UNAUTHORIZED ACCESS ATTEMPT{RESET}")
                time.sleep(1)

            if attempts == 0:
                print(f" {RED}CRITICAL SECURITY LOCK: SYSTEM UNAVAILABLE FOR 60s.{RESET}")
                time.sleep(2); sys.exit()

        elif choice == "2":
            if not users:
                print(f"\n  {YELLOW}⚠️ NO USERS REGISTERED YET. PLEASE REGISTER FIRST.{RESET}")
                time.sleep(1.5); continue
            user_login()

        elif choice == "3":
            user_register()

if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        print(f"\n {RED}Manual interrupt detected. Saving state and exiting...{RESET}")
        sys.exit()