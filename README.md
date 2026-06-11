# PRAAN CORE

## Overview

PRAAN CORE is a web-based Smart Waste Management System developed using Python, Flask, HTML, CSS, and JavaScript. The system simulates waste collection, transportation, processing, and monitoring operations within a smart city environment.

The application provides centralized management of waste bins, collection vehicles, processing facilities, environmental conditions, and citizen interactions through dedicated administrative and user portals.

---

## Objectives

* Automate waste collection monitoring.
* Detect overflow and contamination events.
* Optimize waste collection through intelligent dispatch strategies.
* Manage vehicle operations and maintenance.
* Simulate environmental conditions affecting collection activities.
* Provide citizen interaction through complaints and penalty management.

---

## System Architecture

### Backend

* Python
* Flask Framework
* REST API-based communication

### Frontend

* HTML
* CSS
* JavaScript

### Core Components

* Waste Bin Management
* Fleet Management
* Dispatch Engine
* Processing Facility Management
* Weather and Traffic Simulation
* User Authentication System

---

## Functional Modules

### Authentication Module

Provides login and session management for administrators and citizens.

Functions:

* User registration
* User login
* Session handling
* Access control

---

### Waste Bin Management

Responsible for monitoring waste collection points.

Functions:

* Bin fill level tracking
* Overflow detection
* Contamination detection
* Waste injection simulation
* Bin status monitoring

---

### Dispatch Management

Handles waste collection scheduling and vehicle assignment.

Functions:

* Priority-based dispatch
* Single-bin clearance
* Zone-wise collection
* Full-city collection sweep
* Dynamic route reassignment

---

### Fleet Management

Maintains information regarding collection vehicles.

Functions:

* Fuel monitoring
* Vehicle health tracking
* Maintenance management
* Refueling operations
* Vehicle repair operations

---

### Processing Facility Management

Manages waste processing centers.

Functions:

* Facility load monitoring
* Capacity management
* Temporary storage monitoring
* Waste processing operations

---

### Environmental Monitoring

Simulates external conditions affecting waste collection.

Functions:

* Traffic monitoring
* Road closure simulation
* Rainfall simulation
* Wind monitoring
* Temperature monitoring

---

### Citizen Services

Provides user interaction features.

Functions:

* Complaint submission
* Penalty tracking
* Penalty payment
* Waste disposal simulation

---

## Key Features

* Real-time waste bin monitoring
* Overflow detection and alerts
* Waste contamination tracking
* Dynamic vehicle dispatch
* Fleet maintenance management
* Weather-aware route planning
* Processing facility monitoring
* Administrative dashboard
* Citizen interaction portal
* Complaint and penalty management

---

## Project Structure

```text
PRAAN-CORE/
│
├── app.py
├── proj2.py
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

---

## Technologies Used

| Component     | Technology            |
| ------------- | --------------------- |
| Backend       | Python, Flask         |
| Frontend      | HTML, CSS, JavaScript |
| Architecture  | Client-Server         |
| Communication | REST APIs             |

---

## Execution

Install dependencies:

```bash
pip install flask
```

Run the application:

```bash
python app.py
```

Access the application:

```text
http://127.0.0.1:5000
```

---

## Authors

Developed as a Semester Project by Sai Saranya BL and Team.
