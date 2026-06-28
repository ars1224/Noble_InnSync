# Course: SD203 Investigative Studio 1

# Assessment: Assessment 2 – Team Prototype and Report

# Institution: Yoobee Colleges

# Noble InnSync

Noble InnSync is a hotel booking and operations management system built for the SD203 final prototype. It supports guest room booking, reservation tracking, staff workflows, inventory monitoring, equipment reporting, payments, and management reporting in one Flask application.

## 📖 Final Prototype Status

This version is the completed final prototype for assessment submission. The main guest, staff, admin, and manager workflows are implemented and have been tested through the application UI and Flask test client smoke checks.

## 👥 Team Members

* Dhona Obina – 270248888
* Jhon Aries Tayao – 270556059

## 💻 Technology Stack

* Python
* Flask
* Flask-SQLAlchemy
* Flask-WTF
* Flask-Login
* SQLite
* SQLAlchemy
* Jinja2 Templates
* HTML
* CSS
* JavaScript
* Font Awesome

## 🚀 Quick Start

### Requirements

* Python 3.12 or later
* Git

### Setup

```bash
git clone https://github.com/ars1224/Noble_InnSync.git
cd Noble_InnSync

python -m venv venv
```

Activate the virtual environment:

**Windows PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

```cmd
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create and seed the database:

```bash
python create_db.py
```

Run the application:

```bash
python run.py
```

Open in your browser:

```text
http://localhost:5000
```

### Troubleshooting

If you receive:

```text
ModuleNotFoundError: No module named 'flask_wtf'
```

Run:

```bash
pip install -r requirements.txt
```

All required project packages, including Flask-WTF, Flask-Login, SQLAlchemy, and WTForms, are listed in `requirements.txt`.

## 🏗️ Project Structure

```text
Noble_InnSync/
|-- app/
|   |-- models/
|   |-- routes/
|   |-- static/
|   |-- templates/
|   `-- utils/
|-- create_db.py
|-- requirements.txt
|-- run.py
|-- tests/
`-- README.md
```

## ✨ Features

### Guest Features

* Browse available rooms by date and guest count
* Edit room search directly from the available rooms page
* View room details, photos, capacity, amenities, and pricing
* Smart room allocation for guest capacity
* Complete a booking request
* Server-side validation for guest contact details and card payment fields
* View booking confirmation and reservation status
* Return to the booking homepage from either confirmation flow
* Print or save only the reservation details as PDF (page navigation and footer are excluded)
* Responsive guest interface for desktop, tablet, and mobile

### Staff and Admin Features

* Staff, manager, and admin login
* Role-based dashboard navigation
* Walk-in booking workflow
* Booking management and status updates
* Room status and room inventory management
* Required equipment-issue report before a room is set to Maintenance
* Payment tracking and payment status updates
* Inventory monitoring with working category filters
* Equipment issue reporting and maintenance tracking
* Activity log for operational follow-up
* Manager reports for revenue, bookings, rooms, and payments
* Responsive admin dashboards for desktop, tablet, and medium screens

### Scheduled Booking Lifecycle

* Lapsed active bookings are automatically cancelled after their checkout date has passed
* Paid card payments on lapsed bookings are marked as refunded
* Rooms from cancelled lapsed bookings are released when they are not needed by another active booking
* Cancelled and already checked-out bookings are left unchanged

Run the reconciliation command from Task Scheduler, cron, or a deployment scheduler:

```bash
flask --app run reconcile-bookings
```

This keeps lifecycle writes out of ordinary page requests.

### Room Maintenance Workflow

When staff select `Maintenance` on the Rooms page, Noble InnSync opens a required equipment report containing:

* The selected room
* Equipment name
* Issue status
* Priority
* Issue notes

Submitting the report creates an equipment issue, marks maintenance as requested, records the activity, and moves the room into Maintenance. The same button can be used to report another issue for a room that is already under maintenance.

## 🔐 Staff Accounts

Staff accounts are stored in SQLite with hashed passwords. Create the first account with the Flask CLI; the password is requested through a hidden prompt and is never stored in source code:

```bash
flask --app run create-user --username admin --role admin --full-name "System Admin"
```

List the configured accounts without showing password hashes:

```bash
flask --app run list-users
```

To change an existing account, repeat `create-user` with the `--update` flag.

For production, set a long random `SECRET_KEY` environment variable. Local development automatically creates a private ignored key in `instance/.secret_key`.

Staff login page:

```text
http://localhost:5000/auth/staff-login
```

## ✅ Tested Features

The following workflows have been checked for the final prototype:

* Homepage loads successfully
* Guest room availability search works
* Available rooms page supports inline search editing
* Room details display capacity, room information, and booking actions
* Smart room allocation suggests rooms based on adult and child guest count
* Single rooms are blocked when the guest count exceeds room capacity
* Booking form rejects invalid email, NZ-style phone, and card payment details before saving
* Booking total includes 15% tax/fees across guest and admin workflows
* Failed and pending payment flows release temporary room holds
* Scheduled reconciliation cancels lapsed bookings and refunds paid card records
* Reservation status lookup displays booking details
* Reservation confirmation actions return guests to the booking homepage
* Reservation print/PDF output excludes the site header and footer
* Admin dashboard loads after login
* Room maintenance requires an equipment, status, priority, and notes report
* Maintenance reports create equipment issues and activity records
* Inventory category filters show only matching supply records
* Inventory dashboard supports responsive medium-screen layouts
* Equipment, activity log, room, booking, payment, report, and walk-in pages load after login
* Admin dashboard controls stay inside their cards on medium screen sizes

See [TESTING.md](TESTING.md) for the guest, staff, admin, manager, and responsive testing checklist.

## 🧪 Automated Tests

Run the isolated automated test suite with:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

If your terminal is already inside the `tests` folder, run:

```powershell
..\venv\Scripts\python.exe test_app.py
```

On macOS/Linux with the virtual environment activated, run:

```bash
python -m unittest discover -s tests -v
```

The automated test suite uses an in-memory SQLite database and does not modify the development database. It covers guest booking, payment holds, booking lifecycle reconciliation, room maintenance reporting, inventory filtering and stock operations, equipment resolution, walk-in bookings, booking and payment updates, room CRUD, confirmation navigation, printing rules, authentication, and role permissions.

## 📂 GitHub Repository

https://github.com/ars1224/Noble_InnSync.git

## 📹 Assessment Deliverables

* Complete working prototype
* GitHub repository with regular commits
* Updated README documentation
* Demo video showing the application in action
* Final presentation and supporting assessment documents
