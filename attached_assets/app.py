from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import random
import os
import sqlite3


app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Инициализация базы данных
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE users
                     (username TEXT PRIMARY KEY, password TEXT)''')
        c.execute('''CREATE TABLE progress
                     (username TEXT, task_id INTEGER, completed INTEGER, PRIMARY KEY (username, task_id))''')
        conn.commit()
        conn.close()

init_db()

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Проверка, существует ли пользователь
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        if c.fetchone():
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))
        
        # Добавление нового пользователя
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        
        flash('Регистрация прошла успешно. Теперь вы можете войти.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        if c.fetchone():
            session['username'] = username
            flash('Вы успешно вошли в систему.')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.')
        
        conn.close()
    
    return render_template('login.html')

# Сохранение прогресса
@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def task(task_id):
    if request.method == 'POST':
        username = session.get('username')
        if username:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO progress (username, task_id, completed) VALUES (?, ?, ?)', (username, task_id, 1))
            conn.commit()
            conn.close()
    
    task_data = tasks.get(str(task_id), {"questions": ["нет задачи"], "answers": []})
    return render_template('task.html', task_id=task_id, questions=task_data["questions"], answers=task_data["answers"])

# Остальные маршруты остаются без изменений

# Загрузка задач из JSON файла
def load_tasks():
    if os.path.exists('tasks.json'):
        with open('tasks.json', 'r', encoding='utf-8') as f:
            tasks = json.load(f)
            print("Загруженные задачи из файла:", tasks)  # Отладочное сообщение
            return tasks
    return {}

tasks = load_tasks()

# Загрузка прогресса пользователя из JSON файла
def load_progress(username):
    if os.path.exists('progress.json'):
        with open('progress.json', 'r', encoding='utf-8') as f:
            progress = json.load(f)
            return progress.get(username, {})
    return {}

# Сохранение прогресса пользователя в JSON файл
def save_progress(username, progress):
    if os.path.exists('progress.json'):
        with open('progress.json', 'r', encoding='utf-8') as f:
            all_progress = json.load(f)
    else:
        all_progress = {}

    all_progress[username] = progress

    with open('progress.json', 'w', encoding='utf-8') as f:
        json.dump(all_progress, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/study')
def study():
    return render_template('study.html')

@app.route('/practice')
def practice():
    return render_template('practice.html')

@app.route('/rating')
def rating():
    return render_template('rating.html')

@app.route('/statistics')
def statistics():
    username = session.get('username')
    if username:
        progress = load_progress(username)
        return render_template('statistics.html', progress=progress)
    else:
        flash('Пожалуйста, войдите в систему, чтобы просмотреть статистику.')
        return redirect(url_for('login'))

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
def task(task_id):
    if request.method == 'POST':
        username = session.get('username')
        if username:
            progress = load_progress(username)
            progress[str(task_id)] = True  # Сохраняем, что задача выполнена
            save_progress(username, progress)
    
    task_data = tasks.get(str(task_id), {"questions": ["нет задачи"], "answers": []})
    return render_template('task.html', task_id=task_id, questions=task_data["questions"], answers=task_data["answers"])

@app.route('/random_task')
def random_task():
    task_id = random.choice(list(tasks.keys()))
    return task(task_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        
        # Проверка, существует ли пользователь с таким именем
        if username in users:
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))
        
        # Создание нового пользователя
        users[username] = {'password': password}
        save_users(users)
        
        flash('Регистрация прошла успешно. Теперь вы можете войти.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        
        if username in users and users[username]['password'] == password:
            session['username'] = username  # Сохраняем имя пользователя в сессии
            flash('Вы успешно вошли в систему.')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Удаляем имя пользователя из сессии
    flash('Вы вышли из системы.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)