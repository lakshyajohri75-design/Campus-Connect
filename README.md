# 🎓 CampusConnect

CampusConnect is a web-based platform designed to connect **students and university clubs** in one centralized system.

Students can discover clubs, view club information, apply to join clubs, and track their application status. Clubs can manage their profiles, control recruitment availability, review student applications, and update recruitment decisions through a dedicated dashboard.

The project is built with **Python, Flask, SQLite, HTML, and Jinja2**.

---

## ✨ Features

### 🎓 Student Features

* Student registration and login
* Student dashboard
* Student profile management
* Browse available university clubs
* View individual club details
* Apply to clubs that are accepting applications
* Prevent duplicate applications
* Track submitted applications
* View recruitment/application status

### 🏢 Club Features

* Club registration and login
* Dedicated club dashboard
* Club profile management
* Add club description, benefits, and notices
* Control recruitment status
* View application statistics
* View students who applied
* Review student information
* Update application status

### 📋 Application Management

Applications can move through different recruitment stages:

* 📨 Pending
* 🔍 Under Review
* 🧪 Eligible for Test
* 🎤 Eligible for Interview
* ✅ Selected
* ❌ Rejected

---

## 🛠️ Tech Stack

| Technology         | Purpose                                |
| ------------------ | -------------------------------------- |
| **Python**         | Backend programming                    |
| **Flask**          | Web framework                          |
| **SQLite**         | Database                               |
| **HTML5**          | Frontend structure                     |
| **Jinja2**         | Dynamic HTML templates                 |
| **Flask Sessions** | User authentication/session management |

---

## 🏗️ Project Structure

```text
CampusConnect/
│
├── app.py
├── database.py
├── campusconnect.db
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── student.html
│   ├── club.html
│   ├── student_register.html
│   ├── club_register.html
│   ├── student_dashboard.html
│   ├── student_profile.html
│   ├── student_clubs.html
│   ├── club_details.html
│   ├── student_applications.html
│   ├── club_dashboard.html
│   ├── club_profile.html
│   └── club_applications.html
│
└── README.md
```

> `campusconnect.db` is generated/managed by the application. If you use GitHub, it is generally better to add the database file to `.gitignore` rather than commit local development data.

---

## 🗄️ Database

CampusConnect currently uses SQLite.

### Users

Stores student accounts including:

* ID
* Name
* Email
* Password
* User type

### Clubs

Stores club information including:

* Club ID
* Club name
* University
* Category
* Email
* Password
* Recruitment status
* Description
* Benefits
* Notice

### Applications

The application system connects students with clubs and stores:

* Student
* Club
* Application status
* Application date

### Announcements

The database also contains support for club announcements, including:

* Club
* Announcement title
* Content
* Creation date

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/CampusConnect.git
cd CampusConnect
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Flask

```bash
pip install flask
```

If you create a `requirements.txt` file, you can instead use:

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The Flask development server will start locally.

Open the local address shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

---

## 🔐 User Flow

### Student

```text
Register
   ↓
Student Dashboard
   ↓
Browse Clubs
   ↓
View Club
   ↓
Apply
   ↓
My Applications
   ↓
Track Recruitment Status
```

### Club

```text
Register
   ↓
Club Dashboard
   ↓
Edit Club Profile
   ↓
Set Recruitment Status
   ↓
Receive Applications
   ↓
Review Students
   ↓
Update Application Status
```

---

## 📊 Recruitment Workflow

CampusConnect allows clubs to control their recruitment availability.

Possible recruitment states:

```text
Coming Soon
     ↓
Open
     ↓
Under Review
     ↓
Closed
```

When a club is marked **Open**, students can submit applications.

After applying, the club can progress the student's application through the recruitment stages.

---

## 🔒 Current Security Note

This project is currently intended as a **learning/development project**.

For a production deployment, several security improvements should be implemented, including:

* Password hashing
* Environment-based Flask secret keys
* CSRF protection
* Stronger input validation
* Secure session configuration
* Production database configuration
* Proper error handling
* HTTPS
* Authentication/authorization hardening

Do not use the current development configuration for handling real user credentials.

---

## 🧠 Future Improvements

Potential future versions of CampusConnect could include:

* 🔔 Club announcements
* 👥 Club teams and member management
* 🔎 Advanced club search and filtering
* 📱 Responsive/mobile-friendly UI
* 📧 Email notifications
* 📊 Advanced recruitment analytics
* 🖼️ Club logos and images
* 🔐 Improved authentication
* 🤖 AI-based club/student recommendations
* ☁️ Cloud deployment
* 🗃️ PostgreSQL/MySQL support

---

## 🎯 Project Goal

The goal of CampusConnect is to make university club recruitment more organized and accessible.

Instead of students searching for club information through scattered sources and clubs handling applications manually, CampusConnect provides a single platform where both sides can manage the recruitment process.

---

##  Current Status

**CampusConnect is currently an active development project.**

The core student-club recruitment workflow is implemented, including registration, authentication, club discovery, applications, dashboards, and application status management.

Additional features and UI improvements can be added as the project evolves.

---

## 👨‍💻 Built With

**Python • Flask • SQLite • HTML • Jinja2**

---

## 📄 License

This project can be released under the **MIT License** if you want it to be open-source.

If you choose MIT, add a `LICENSE` file to the repository containing the standard MIT License text.
