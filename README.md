# Course: SD203 Investigative Studio 1

# Assessment: Assessment 2 – Team Prototype and Report

# Institution: Yoobee Colleges

# Noble InnSync

Noble InnSync is a hotel booking and operations management system built for the SD203 final prototype. It supports guest room booking, reservation tracking, staff workflows, inventory monitoring, equipment reporting, payments, and management reporting in one Flask application.

## 📖 Final Prototype Status

This version is the completed final prototype for assessment submission. The main guest, staff, admin, and manager workflows are implemented and have been tested through the application UI and Flask test client smoke checks.

## 👥 Team Members

- Dhona Obina – 270248888
- Jhon Aries Tayao – 270556059

## 💻 Technology Stack

- Python
- Flask
- Jinja2 templates
- SQLite
- Flask-SQLAlchemy / SQLAlchemy
- HTML
- CSS
- JavaScript
- Font Awesome icons

## 🏗️ Project Structure

```text
Noble_InnSync/
|-- app/
|   |-- models/          Database models
|   |-- routes/          Flask route handlers
|   |-- static/          CSS, JavaScript, and images
|   |-- templates/       Jinja2 page templates
|   `-- utils/           Shared helper functions
|-- create_db.py         Database setup and seed script
|-- requirements.txt     Python dependencies
|-- run.py               Application entry point
|-- tests/               Isolated Flask regression tests
`-- README.md
```

## ✨ Features

### Guest Features

- Browse available rooms by date and guest count
- Edit room search directly from the available rooms page
- View room details, photos, capacity, amenities, and pricing
- Smart room allocation for guest capacity
- Complete a booking request
- View booking confirmation and reservation status
- Return to the booking homepage from either confirmation flow
- Print or save only the reservation details as PDF (page navigation and footer are excluded)
- Responsive guest interface for desktop, tablet, and mobile

### Staff and Admin Features

- Staff, manager, and admin login
- Role-based dashboard navigation
- Walk-in booking workflow
- Booking management and status updates
- Room status and room inventory management
- Required equipment-issue report before a room is set to Maintenance
- Payment tracking and payment status updates
- Inventory monitoring with working category filters
- Equipment issue reporting and maintenance tracking
- Activity log for operational follow-up
- Manager reports for revenue, bookings, rooms, and payments
- Responsive admin dashboards for desktop, tablet, and medium screens

### Automated Booking Lifecycle

- Active bookings are automatically cancelled after their checkout date has passed
- Paid card transactions attached to lapsed bookings are marked as Refunded
- Rooms from lapsed bookings are released when they are not needed by another active booking
- Cancelled and already checked-out bookings are left unchanged

### Room Maintenance Workflow

When staff select `Maintenance` on the Rooms page, Noble InnSync opens a required
equipment report containing:

- The selected room
- Equipment name
- Issue status
- Priority
- Issue notes

Submitting the report creates an equipment issue, marks maintenance as requested,
records the activity, and moves the room into Maintenance. The same button can be
used to report another issue for a room that is already under maintenance.

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/ars1224/Noble_InnSync.git
```

2. Navigate to the project folder:

```bash
cd Noble_InnSync
```

3. Create a virtual environment:

```bash
python -m venv venv
```

4. Activate the virtual environment.

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Create and seed the local database:

```bash
python create_db.py
```

## ▶️ Running the Application

Start the Flask application:

```bash
python run.py
```

Open the app in a browser:

```text
http://localhost:5000
```

## 🔐 Staff Accounts

Staff accounts are stored in SQLite with hashed passwords. Create the first account
with the Flask CLI; the password is requested through a hidden prompt and is never
stored in source code:

```bash
flask --app run create-user --username admin --role admin --full-name "System Admin"
```

List the configured accounts without showing password hashes:

```bash
flask --app run list-users
```

To change an existing account, repeat `create-user` with the `--update` flag.

For production, set a long random `SECRET_KEY` environment variable. Local
development automatically creates a private ignored key in `instance/.secret_key`.

Staff login page:

```text
http://localhost:5000/auth/staff-login
```

## ✅ Tested Features

The following workflows have been checked for the final prototype:

- Homepage loads successfully
- Guest room availability search works
- Available rooms page supports inline search editing
- Room details display capacity, room information, and booking actions
- Smart room allocation suggests rooms based on adult and child guest count
- Single rooms are blocked when the guest count exceeds room capacity
- Booking total includes 15% tax/fees across guest and admin workflows
- Failed and pending payment flows release temporary room holds
- Lapsed active bookings are cancelled automatically and paid card records are refunded
- Reservation status lookup displays booking details
- Reservation confirmation actions return guests to the booking homepage
- Reservation print/PDF output excludes the site header and footer
- Admin dashboard loads after login
- Room maintenance requires an equipment, status, priority, and notes report
- Maintenance reports create equipment issues and activity records
- Inventory category filters show only matching supply records
- Inventory dashboard supports responsive medium-screen layouts
- Equipment, activity log, room, booking, payment, report, and walk-in pages load after login
- Admin dashboard controls stay inside their cards on medium screen sizes

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

The 22-test suite uses an in-memory SQLite database and does not modify the
development database. It covers guest booking, payment holds, lapse/refund
handling, room maintenance reporting, inventory filtering and stock operations,
equipment resolution, walk-in bookings, booking and payment updates, room CRUD,
confirmation navigation, printing rules, authentication, and role permissions. See
[TESTING.md](TESTING.md) for the full automated and manual testing checklist.

## 📂 GitHub Repository

https://github.com/ars1224/Noble_InnSync.git

## 📹 Assessment Deliverables

- Complete working prototype
- GitHub repository with regular commits
- Updated README documentation
- Demo video showing the application in action
- Final presentation and supporting assessment documents
