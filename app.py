from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# 数据库连接
def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.environ['DB_NAME'],      # 从环境变量获取数据库名称
        user=os.environ['DB_USER'],        # 从环境变量获取用户名
        password=os.environ['DB_PASSWORD'], # 从环境变量获取密码
        host=os.environ['DB_HOST'],         # 从环境变量获取主机
        port=os.environ['DB_PORT']          # 从环境变量获取端口
    )
    return conn

# 初始化数据库并创建表
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')

    # 创建会员表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            name TEXT,
            contact TEXT,
            recharge_amount REAL,
            balance REAL
        )
    ''')

    # 创建销售记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            date TEXT,
            activity TEXT,
            sessions INTEGER,
            dm TEXT,
            players TEXT,
            income REAL,
            expenses REAL,
            profit REAL,
            total REAL
        )
    ''')

    # 添加默认用户
    users = [
        ('xuezhang', '123459876'),
        ('qianqian', '123459876'),
        ('tudousi', '123459876')
    ]
    for username, password in users:
        hashed_password = generate_password_hash(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING;", (username, hashed_password))

    conn.commit()
    cursor.close()
    conn.close()

# 登录页面
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user[0], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    
    return render_template('login.html')

# 仪表盘页面
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# 会员管理页面路由
@app.route('/members')
def members():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, contact, recharge_amount, balance FROM members")
    members = cursor.fetchall()
    cursor.close()
    conn.close()
    
    members_data = [
        {
            "name": member[0],
            "contact": member[1],
            "recharge_amount": member[2] if member[2] is not None else 0,
            "balance": member[3] if member[3] is not None else 0
        }
        for member in members
    ]
    
    return render_template('members.html', members_data=members_data)

# 销售记录页面路由
@app.route('/sales')
def sales():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, activity, sessions, dm, players, income, expenses, profit, total FROM sales")
    sales = cursor.fetchall()
    cursor.close()
    conn.close()
    
    sales_data = [
        {
            "date": sale[0],
            "activity": sale[1],
            "sessions": sale[2],
            "dm": sale[3],
            "players": sale[4],
            "income": sale[5] if sale[5] is not None else 0,
            "expenses": sale[6] if sale[6] is not None else 0,
            "profit": sale[7] if sale[7] is not None else 0,
            "total": sale[8] if sale[8] is not None else 0
        }
        for sale in sales
    ]
    
    return render_template('sales.html', sales_data=sales_data)

# 批量保存会员数据的路由
@app.route('/save_members', methods=['POST'])
def save_members():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 清空表然后重新插入所有数据
    cursor.execute("DELETE FROM members")
    for row in data:
        if row[0] and row[1]:  # 确保名字和电话不为空
            cursor.execute("INSERT INTO members (name, contact, recharge_amount, balance) VALUES (%s, %s, %s, %s)",
                           (row[0], row[1], row[2] if row[2] else 0, row[3] if row[3] else 0))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"}), 200

# 批量保存销售数据的路由
@app.route('/save_sales', methods=['POST'])
def save_sales():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 清空表然后重新插入所有数据
    cursor.execute("DELETE FROM sales")
    for row in data:
        if row[0] and row[1]:  # 确保日期和活动名称不为空
            cursor.execute("INSERT INTO sales (date, activity, sessions, dm, players, income, expenses, profit, total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (row[0], row[1], row[2] if row[2] else 0, row[3], row[4], row[5] if row[5] else 0, row[6] if row[6] else 0, row[7] if row[7] else 0, row[8] if row[8] else 0))
    
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"}), 200

# 退出登录
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

   
