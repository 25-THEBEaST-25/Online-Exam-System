from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import mysql.connector
from mysql.connector import Error
import hashlib
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'examSystem2024SecretKey'

# ─── DATABASE CONFIGURATION ───────────────────────────────────────────────────
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'PHW#84#jeor',
    'database': 'online_exam_db'
}

def get_db():
    """Get a fresh DB connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"DB connection error: {e}")
        flash('Database connection failed. Check MySQL service.', 'error')
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ─── INIT DATABASE ─────────────────────────────────────────────────────────────
def init_db():
    conn = get_db()
    if not conn:
        return
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            role ENUM('admin','student') NOT NULL DEFAULT 'student',
            email VARCHAR(150),
            full_name VARCHAR(150)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            exam_name VARCHAR(200) NOT NULL,
            duration INT NOT NULL DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active TINYINT(1) DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            exam_id INT NOT NULL,
            question TEXT NOT NULL,
            option1 VARCHAR(300) NOT NULL,
            option2 VARCHAR(300) NOT NULL,
            option3 VARCHAR(300) NOT NULL,
            option4 VARCHAR(300) NOT NULL,
            correct_answer TINYINT NOT NULL,
            FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            exam_id INT NOT NULL,
            score INT NOT NULL DEFAULT 0,
            total INT NOT NULL DEFAULT 0,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (exam_id) REFERENCES exams(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            exam_id INT NOT NULL,
            status ENUM('present', 'absent') NOT NULL DEFAULT 'present',
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id),
            FOREIGN KEY (exam_id) REFERENCES exams(id),
            UNIQUE KEY unique_student_exam (student_id, exam_id)
        )
    """)

    # Seed default admin with correct hash
    correct_hash = '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'
    cursor.execute("SELECT id FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password, role, full_name) VALUES (%s,%s,'admin','Administrator')",
            ('admin', correct_hash)
        )

    conn.commit()
    cursor.close()
    conn.close()


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = hash_password(request.form['password'])
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close(); conn.close()
        if user:
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['role']      = user['role']
            session['full_name'] = user['full_name'] or user['username']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE role='student'")
    student_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM exams")
    exam_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM results")
    result_count = cursor.fetchone()['cnt']
    cursor.execute("""
        SELECT r.*, u.full_name, e.exam_name
        FROM results r
        JOIN users u ON r.student_id=u.id
        JOIN exams e ON r.exam_id=e.id
        ORDER BY r.attempted_at DESC LIMIT 10
    """)
    recent_results = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('admin.html',
        student_count=student_count,
        exam_count=exam_count,
        result_count=result_count,
        recent_results=recent_results
    )


# ADD EXAM
@app.route('/admin/add_exam', methods=['GET', 'POST'])
def add_exam():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        exam_name = request.form['exam_name'].strip()
        duration  = int(request.form['duration'])
        conn = get_db()
        if not conn:
            flash('Database error. Try again.', 'error')
            return render_template('add_exam.html')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO exams (exam_name, duration) VALUES (%s,%s)", (exam_name, duration))
            exam_id = cursor.lastrowid

            questions = request.form.getlist('question[]')
            opt1 = request.form.getlist('option1[]')
            opt2 = request.form.getlist('option2[]')
            opt3 = request.form.getlist('option3[]')
            opt4 = request.form.getlist('option4[]')
            correct = request.form.getlist('correct[]')

            for i, q in enumerate(questions):
                if q.strip():
                    cursor.execute("""
                        INSERT INTO questions (exam_id, question, option1, option2, option3, option4, correct_answer)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (exam_id, q, opt1[i], opt2[i], opt3[i], opt4[i], int(correct[i])))
            conn.commit()
            flash('Exam created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Error as e:
            flash('Error creating exam.', 'error')
        finally:
            cursor.close(); conn.close()
    return render_template('add_exam.html')


# VIEW ALL EXAMS
@app.route('/admin/exams')
def view_exams():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    if not conn:
        flash('Database unavailable.', 'error')
        return render_template('view_exams.html', exams=[])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, COUNT(q.id) AS question_count
        FROM exams e
        LEFT JOIN questions q ON e.id=q.exam_id
        GROUP BY e.id
        ORDER BY e.created_at DESC
    """)
    exams = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('view_exams.html', exams=exams)


# DELETE EXAM
@app.route('/admin/delete_exam/<int:exam_id>')
def delete_exam(exam_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exams WHERE id=%s", (exam_id,))
    conn.commit()
    cursor.close(); conn.close()
    flash('Exam deleted.', 'success')
    return redirect(url_for('view_exams'))


# MANAGE STUDENTS
@app.route('/admin/students', methods=['GET'])
def manage_students():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    if not conn:
        flash('Database unavailable.', 'error')
        return render_template('students.html', students=[])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC")
    students = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('students.html', students=students)


# ADD STUDENT (Admin)
@app.route('/admin/add_student', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    full_name = request.form['full_name'].strip()
    username  = request.form['username'].strip()
    email     = request.form['email'].strip()
    password  = hash_password(request.form['password'])
    conn = get_db()
    if not conn:
        flash('Database error.', 'error')
        return redirect(url_for('manage_students'))
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role, email, full_name) VALUES (%s,%s,'student',%s,%s)",
            (username, password, email, full_name)
        )
        conn.commit()
        flash('Student added successfully!', 'success')
    except Error:
        flash('Username already exists.', 'error')
    finally:
        cursor.close(); conn.close()
    return redirect(url_for('manage_students'))


# VIEW RESULTS (Admin)
@app.route('/admin/results', methods=['GET'])
def all_results():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db()
    if not conn:
        flash('Database unavailable.', 'error')
        return render_template('all_results.html', results=[])
    cursor = conn.cursor(dictionary=True)
    student_id = request.args.get('student')
    if student_id:
        cursor.execute("""
            SELECT r.*, u.full_name, u.username, e.exam_name
            FROM results r
            JOIN users u ON r.student_id=u.id
            JOIN exams e ON r.exam_id=e.id
            WHERE r.student_id = %s
            ORDER BY r.attempted_at DESC
        """, (student_id,))
    else:
        cursor.execute("""
            SELECT r.*, u.full_name, u.username, e.exam_name
            FROM results r
            JOIN users u ON r.student_id=u.id
            JOIN exams e ON r.exam_id=e.id
            ORDER BY r.attempted_at DESC
        """)
    results = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('all_results.html', results=results)


# ─── STUDENT ROUTES ───────────────────────────────────────────────────────────

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT e.*, COUNT(q.id) AS question_count FROM exams e LEFT JOIN questions q ON e.id=q.exam_id WHERE e.is_active=1 GROUP BY e.id")
    exams = cursor.fetchall()
    cursor.execute("""
        SELECT r.*, e.exam_name FROM results r
        JOIN exams e ON r.exam_id=e.id
        WHERE r.student_id=%s ORDER BY r.attempted_at DESC
    """, (session['user_id'],))
    my_results = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) AS cnt FROM results WHERE student_id=%s", (session['user_id'],))
    completed_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) AS cnt FROM attendance WHERE student_id=%s AND status='absent'", (session['user_id'],))
    absence_count = cursor.fetchone()['cnt']
    cursor.close(); conn.close()
    return render_template('student_dashboard.html', exams=exams, my_results=my_results, completed_count=completed_count, absence_count=absence_count)


@app.route('/student/report.pdf')
def student_report():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT full_name, username FROM users WHERE id=%s", (session['user_id'],))
    student = cursor.fetchone()
    cursor.execute("""
        SELECT r.*, e.exam_name FROM results r
        JOIN exams e ON r.exam_id=e.id
        WHERE r.student_id=%s ORDER BY r.attempted_at DESC
    """, (session['user_id'],))
    results = cursor.fetchall()
    cursor.execute("""
        SELECT a.*, e.exam_name FROM attendance a
        JOIN exams e ON a.exam_id=e.id
        WHERE a.student_id=%s AND a.status='absent' ORDER BY a.marked_at DESC
    """, (session['user_id'],))
    absences = cursor.fetchall()
    cursor.close(); conn.close()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"Exam Report - {student['full_name']} ({student['username']})", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Stats
    stats_data = [
        ['Metric', 'Count'],
        ['Completed Exams', len(results)],
        ['Absences', len(absences)]
    ]
    stats_table = Table(stats_data)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 12))
    
    # Completed Exams
    if results:
        story.append(Paragraph("Completed Exams", styles['Heading2']))
        results_data = [['Exam', 'Score', 'Total', 'Percentage', 'Date']]
        for r in results:
            pct = round((r['score']/r['total'])*100) if r['total'] else 0
            results_data.append([r['exam_name'], f"{r['score']}/{r['total']}", pct, r['attempted_at'].strftime('%Y-%m-%d')])
        results_table = Table(results_data)
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,0), 12)
        ]))
        story.append(results_table)
        story.append(Spacer(1, 12))
    
    # Absences
    if absences:
        story.append(Paragraph("Marked Absences", styles['Heading2']))
        abs_data = [['Exam', 'Marked Date']]
        for a in absences:
            abs_data.append([a['exam_name'], a['marked_at'].strftime('%Y-%m-%d')])
        abs_table = Table(abs_data)
        abs_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.red),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,0), 12)
        ]))
        story.append(abs_table)
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"exam_report_{student['username']}.pdf", mimetype='application/pdf')


# REGISTER (Student self-register)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        username  = request.form['username'].strip()
        email     = request.form['email'].strip()
        password  = hash_password(request.form['password'])
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, email, full_name) VALUES (%s,%s,'student',%s,%s)",
                (username, password, email, full_name)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Error:
            flash('Username already exists. Try another.', 'error')
        finally:
            cursor.close(); conn.close()
    return render_template('register.html')


# START EXAM
@app.route('/exam/<int:exam_id>')
def start_exam(exam_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    # Prevent re-attempt
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM results WHERE student_id=%s AND exam_id=%s",
                   (session['user_id'], exam_id))
    already = cursor.fetchone()
    if already:
        flash('You have already attempted this exam.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('student_dashboard'))

    cursor.execute("SELECT * FROM exams WHERE id=%s", (exam_id,))
    exam = cursor.fetchone()
    cursor.execute("SELECT * FROM questions WHERE exam_id=%s ORDER BY id", (exam_id,))
    questions = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('exam.html', exam=exam, questions=questions)


# SUBMIT EXAM
@app.route('/submit_exam/<int:exam_id>', methods=['POST'])
def submit_exam(exam_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions WHERE exam_id=%s", (exam_id,))
    questions = cursor.fetchall()

    score = 0
    total = len(questions)
    detailed = []
    for q in questions:
        qid = str(q['id'])
        student_ans = request.form.get(f'q_{qid}')
        correct = str(q['correct_answer'])
        is_correct = student_ans == correct
        if is_correct:
            score += 1
        detailed.append({
            'question': q['question'],
            'options': [q['option1'], q['option2'], q['option3'], q['option4']],
            'student_answer': int(student_ans) if student_ans else None,
            'correct_answer': int(correct),
            'is_correct': is_correct
        })

    cursor2 = conn.cursor()
    cursor2.execute(
        "INSERT INTO results (student_id, exam_id, score, total) VALUES (%s,%s,%s,%s)",
        (session['user_id'], exam_id, score, total)
    )
    conn.commit()
    cursor.close(); cursor2.close(); conn.close()

    return render_template('result.html',
        score=score, total=total,
        percentage=round((score/total)*100) if total else 0,
        detailed=detailed
    )


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', debug=True, port=5000)

