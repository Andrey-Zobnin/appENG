#!/usr/bin/env python3
import os
import json
import random
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
DATABASE_FILE = 'database.db'

# Initialize database
def init_db():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        # Create users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, 
                      email TEXT UNIQUE, 
                      password TEXT, 
                      role TEXT DEFAULT 'user')''')
        # Create progress table
        c.execute('''CREATE TABLE IF NOT EXISTS progress
                     (username TEXT, 
                      task_id INTEGER, 
                      completed INTEGER DEFAULT 0,
                      PRIMARY KEY (username, task_id),
                      FOREIGN KEY (username) REFERENCES users(username))''')
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Data handling functions (unchanged from original)
def load_tasks():
    """Load tasks from the JSON file."""
    if os.path.exists(TASKS_FILE) and os.path.getsize(TASKS_FILE) > 0:
        try:
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                logger.info(f"Loaded {len(tasks)} tasks from file")
                return tasks
        except json.JSONDecodeError:
            logger.error(f"Error parsing {TASKS_FILE}, it may be corrupted")
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")

    logger.warning(f"{TASKS_FILE} does not exist or is empty, using empty tasks dictionary")
    return {}

def get_user_progress(username):
    """Get progress for a specific user from the database."""
    progress = {}
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute('SELECT task_id, completed FROM progress WHERE username = ?', (username,))
        for row in c.fetchall():
            progress[str(row[0])] = bool(row[1])
        conn.close()
    except Exception as e:
        logger.error(f"Error getting progress for user {username}: {e}")

    return progress

def save_user_progress(username, task_id, completed=True):
    """Save user progress to the database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO progress (username, task_id, completed) VALUES (?, ?, ?)',
                 (username, task_id, 1 if completed else 0))
        conn.commit()
        conn.close()
        logger.info(f"Saved progress for user {username}, task {task_id}, completed: {completed}")
        return True
    except Exception as e:
        logger.error(f"Error saving progress for user {username}, task {task_id}: {e}")
        return False

# Constants for file paths (unchanged from original)
TASKS_FILE = 'tasks.json'
USERS_FILE = 'users.json'
PROGRESS_FILE = 'progress.json'
DATABASE_FILE = 'database.db'

# Create directory for database if it doesn't exist (unchanged from original)
os.makedirs(os.path.dirname(DATABASE_FILE) if os.path.dirname(DATABASE_FILE) else '.', exist_ok=True)

# Migrate existing users from JSON if exists (unchanged from original)
def migrate_json_users_to_db(conn):
    """Migrate users from JSON file to SQLite database."""
    if os.path.exists(USERS_FILE) and os.path.getsize(USERS_FILE) > 0:
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)
                c = conn.cursor()

                for username, user_data in users.items():
                    c.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)',
                             (username, user_data.get('password', '')))

                conn.commit()
                logger.info(f"Migrated {len(users)} users from JSON to database")
        except json.JSONDecodeError:
            logger.warning(f"Could not parse users from {USERS_FILE}, it may be empty or malformed")
        except Exception as e:
            logger.error(f"Error migrating users from JSON: {e}")

# Global variable to store tasks (unchanged from original)
tasks = load_tasks()

# Routes (unchanged except register, login, logout)
@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/study')
def study():
    """Render the study page."""
    return render_template('study.html')

@app.route('/practice')
def practice():
    """Render the practice page."""
    return render_template('practice.html')

@app.route('/rating')
def rating():
    """Render the ratings page."""
    return render_template('rating.html')

@app.route('/statistics')
def statistics():
    """Render the statistics page showing user progress."""
    username = session.get('username')
    if not username:
        flash('Пожалуйста, войдите в систему, чтобы просмотреть статистику.')
        return redirect(url_for('login'))

    progress = get_user_progress(username)
    return render_template('statistics.html', progress=progress)

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def task(task_id):
    """Render a specific task and handle answer submission."""
    task_id_str = str(task_id)
    username = session.get('username')
    user_role = None
    if username:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute('SELECT role FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        if result:
            user_role = result[0]
        conn.close()

    if request.method == 'POST':
        if username:
            save_user_progress(session['username'], task_id)

    # Get task data or default to empty task
    task_data = tasks.get(task_id_str, {"questions": ["нет задачи"], "answers": []})

    show_answers = user_role == 'admin' #Example role check.  Adjust as needed.

    return render_template('task.html', 
                           task_id=task_id, 
                           questions=task_data["questions"], 
                           answers=task_data["answers"],
                           show_answers=show_answers)

@app.route('/random_task')
def random_task():
    """Redirect to a random task."""
    if not tasks:
        flash('Нет доступных задач.')
        return redirect(url_for('index'))

    task_id = random.choice(list(tasks.keys()))
    return redirect(url_for('task', task_id=task_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db()
            c = conn.cursor()

            # Check if user exists
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            if c.fetchone():
                flash('Пользователь с таким именем уже существует')
                return redirect(url_for('register'))

            # Add new user
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     (username, password, 'user')) # Default role is 'user'
            conn.commit()
            conn.close()

            # Auto login after registration
            session['username'] = username
            flash('Регистрация успешна!')
            return redirect(url_for('index'))

        except Exception as e:
            logger.error(f"Error during registration: {e}")
            flash('Ошибка при регистрации')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                     (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session['username'] = username
                flash('Вы успешно вошли в систему')
                return redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль')

        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash('Ошибка при входе в систему')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Вы вышли из системы')
    return redirect(url_for('login'))

@app.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        email = request.form['email']
        message = request.form['message']
        
        # Сохраняем сообщение в файл
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('support_messages.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n=== {timestamp} ===\n")
            f.write(f"От: {email}\n")
            f.write(f"Сообщение: {message}\n")
        
        try:
            # Отправляем email
            msg = MIMEText(f"От: {email}\n\nСообщение:\n{message}")
            msg['Subject'] = 'Новое сообщение в тех. поддержку'
            msg['From'] = email
            msg['To'] = 'x@mail.ru'
            
            # Настройки SMTP для mail.ru
            smtp_server = 'smtp.mail.ru'
            smtp_port = 587
            smtp_user = 'your-email@mail.ru'  # Замените на ваш email
            smtp_password = 'your-password'    # Замените на ваш пароль
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            flash('Ваше сообщение успешно отправлено!')
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            flash('Сообщение сохранено, но возникла ошибка при отправке email.')
        
        return redirect(url_for('support'))
    
    return render_template('support.html')


# Application entry point (unchanged from original)
if __name__ == '__main__':
    # Initialize database before starting the app
    init_db()

    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)