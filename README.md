# Noble_InnSync

## 🏗️ Project Architecture

Noble InnSync is developed using Flask with an MVC-inspired architecture, allowing clear separation between routes, database models, templates, and static assets for improved maintainability, scalability, and team collaboration.

Project Structure:

app/
├── models/
├── routes/
├── templates/
├── static/
└── **init**.py

## 📖 Project Overview

Noble InnSync is a hotel booking and management system designed to streamline room reservations, customer management, and administrative operations. The application provides an intuitive interface for guests and administrators while maintaining efficient booking workflows.

## 👥 Team Members

* Dhona Obina
* Aries Tayao

## 💻 Technologies Used

* React JS – Frontend user interface
* Tailwind CSS – Styling and responsive design
* Flask – Backend API and server-side logic
* SQLite – Database for rooms, bookings, and users
* GitHub – Version control and collaboration

## ✨ Features

### Guest Features

* Browse available rooms
* View room details
* Make reservations
* Responsive user interface

### Admin Features

* Manage room listings
* View reservations
* Update booking information
* Dashboard overview

## ⚙️ Installation

1. Clone the repository

```bash
git clone [repository-link]
```

2. Navigate to the project folder

```bash
cd Noble_InnSync
```

3. Create a virtual environment

```bash
python -m venv venv
```

4. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

5. Install dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Running the Application

Start the Flask server:

```bash
flask run
```

or

```bash
python run.py
```

Open your browser and visit:

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

## 🗄️ Database

Database: SQLite

Main entities:

* Users
* Rooms
* Reservations
* Bookings

## 📂 GitHub Repository

[Insert GitHub Repository Link]

## 🚧 Known Issues / Future Improvements

* Additional UI refinements
* Enhanced booking validation
* Improved reporting features
* Additional testing and bug fixes

## 📹 Assessment Deliverables

* Working prototype
* GitHub repository
* README documentation
* IPPR report
* Demo video
* Presentation

Updated README.md file


