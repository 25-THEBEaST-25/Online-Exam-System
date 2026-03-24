# 📋 ExamCloud — Cloud-Based Online Examination System

A complete MCQ-based online examination system built with **Flask + MySQL**.
Designed for university mini-projects (MU pattern).

---

## ✅ Features
| Feature | Details |
|---|---|
| Student Login | Session-based authentication |
| Admin Login | Separate admin panel |
| Create Exam | Add MCQ questions with 4 options |
| Timed Exam | Countdown timer, auto-submit on expiry |
| Auto Evaluation | Compare answers → instant score |
| Instant Result | Score ring animation + per-question breakdown |
| Prevent Re-attempt | Each student can attempt an exam only once |
| Grade system | Distinction / First Class / Pass / Fail |

---

## 🗂️ Folder Structure
```
online-exam-system/
├── app.py                 ← Flask backend (all routes)
├── requirements.txt       ← Python dependencies
├── setup_db.sql           ← MySQL schema + seed data
├── README.md
├── templates/
│   ├── login.html         ← Login page
│   ├── register.html      ← Student self-registration
│   ├── admin.html         ← Admin dashboard
│   ├── add_exam.html      ← Create exam + questions
│   ├── view_exams.html    ← List & delete exams
│   ├── students.html      ← Manage students
│   ├── all_results.html   ← All exam results
│   ├── student_dashboard.html  ← Student home
│   ├── exam.html          ← Live exam with timer
│   └── result.html        ← Instant result page
└── static/
    └── style.css          ← Global styles
```

---

## ⚙️ Setup Instructions

### Step 1 — Install Requirements
```bash
pip install -r requirements.txt
```

### Step 2 — Create MySQL Database
```bash
mysql -u root -p < setup_db.sql
```

### Step 3 — Update DB Config in app.py
Open `app.py` and edit:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_MYSQL_PASSWORD',   ← change this
    'database': 'online_exam_db'
}
```

### Step 4 — Run the App
```bash
python app.py
```
Open → **http://localhost:5000**

---

## 🔐 Default Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Student | Register at `/register` | — |

---

## 🗄️ Database Tables

### users
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | Auto increment |
| username | VARCHAR(100) | Unique |
| password | VARCHAR(255) | SHA-256 hash |
| role | ENUM | admin / student |
| email | VARCHAR(150) | Optional |
| full_name | VARCHAR(150) | Display name |

### exams
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| exam_name | VARCHAR(200) | |
| duration | INT | Minutes |
| is_active | TINYINT | 1=visible to students |

### questions
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| exam_id | INT FK | → exams.id |
| question | TEXT | |
| option1–4 | VARCHAR(300) | A,B,C,D |
| correct_answer | TINYINT | 1=A, 2=B, 3=C, 4=D |

### results
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| student_id | INT FK | → users.id |
| exam_id | INT FK | → exams.id |
| score | INT | Correct answers |
| total | INT | Total questions |
| attempted_at | TIMESTAMP | Auto |

---

## 🔄 Auto-Evaluation Logic
```
Student submits → Backend fetches correct_answer for each question_id
                → Compares with student's submitted answers
                → score = count of matches
                → Saves to results table
                → Renders result page instantly
```

## ⏱️ Timer Logic
```javascript
var timeLeft = duration * 60;         // e.g. 600 seconds for 10 min
setInterval(function() {
    timeLeft--;
    if (timeLeft <= 0) {
        document.getElementById('examForm').submit();  // Auto-submit
    }
}, 1000);
```

---

## 🌐 Routes Summary
| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | /login | Login |
| GET | /logout | Logout |
| GET/POST | /register | Student registration |
| GET | /admin | Admin dashboard |
| GET/POST | /admin/add_exam | Create exam |
| GET | /admin/exams | View all exams |
| GET | /admin/delete_exam/<id> | Delete exam |
| GET | /admin/students | Manage students |
| POST | /admin/add_student | Add student |
| GET | /admin/results | All results |
| GET | /student | Student dashboard |
| GET | /exam/<id> | Start exam |
| POST | /submit_exam/<id> | Submit exam |

---

## 📦 Tech Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.x + Flask
- **Database**: MySQL + mysql-connector-python
- **Auth**: Flask sessions + SHA-256 password hashing
