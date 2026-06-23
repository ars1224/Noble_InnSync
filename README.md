# Noble InnSync

Noble InnSync is a hotel booking and operations management system built for the SD203 final prototype. It supports guest room booking, reservation tracking, staff workflows, inventory monitoring, equipment reporting, payments, and management reporting in one Flask application.

## 📖 Final Prototype Status

This version is the completed final prototype for assessment submission. The main guest, staff, admin, and manager workflows are implemented and have been tested through the application UI and Flask test client smoke checks.

## 👥 Team Members

- Dhona Obina
- Aries Tayao

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
- Print or save reservation details as PDF using the browser print dialog
- Responsive guest interface for desktop, tablet, and mobile

### Staff and Admin Features

- Staff, manager, and admin login
- Role-based dashboard navigation
- Walk-in booking workflow
- Booking management and status updates
- Room status and room inventory management
- Payment tracking and payment status updates
- Inventory monitoring for hotel supplies
- Equipment issue reporting and maintenance tracking
- Activity log for operational follow-up
- Manager reports for revenue, bookings, rooms, and payments
- Responsive admin dashboards for desktop, tablet, and medium screens

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
python -m venv .venv
```

4. Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
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

## 🔐 Test Credentials

Use these accounts to test the staff workspace:

| Role | Username | Password |
| --- | --- | --- |
| Admin | admin | admin123 |
| Staff | staff | staff123 |
| Manager | manager | manager123 |

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
- Reservation status lookup displays booking details
- Reservation details can be printed or saved as PDF from the browser
- Admin dashboard loads after login
- Inventory dashboard loads and supports responsive medium-screen layouts
- Equipment, activity log, room, booking, payment, report, and walk-in pages load after login
- Admin dashboard controls stay inside their cards on medium screen sizes

## 🧪 Smoke Test Commands

Run a basic application smoke test with:

```bash
python -c "from app import create_app; app=create_app(); c=app.test_client(); print(c.get('/').status_code); print(c.get('/reservation-status').status_code)"
```

Expected output:

```text
200
200
```

## 📂 GitHub Repository

https://github.com/ars1224/Noble_InnSync.git

## 📹 Assessment Deliverables

- Complete working prototype
- GitHub repository with regular commits
- Updated README documentation
- Demo video showing the application in action
- Final presentation and supporting assessment documents
