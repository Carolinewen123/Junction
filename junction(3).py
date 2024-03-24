from flask import Flask, request, redirect, url_for, session
from flask_session import Session
import os
from functools import wraps
from flask import jsonify
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 设置一个安全密钥
app.config['SESSION_TYPE'] = 'filesystem'  # 将会话数据存储在文件系统中
Session(app)

def save_activity(activity_data):
    activity_data['time'] = datetime.now().isoformat()
    with open('activities.txt', 'a') as file:
        # 将活动数据保存为JSON
        file.write(json.dumps(activity_data) + '\n')

def save_idea(idea, username):
    with open('ideas.txt', 'a') as file:
        # 将建议、用户名和当前时间一起保存
        file.write(json.dumps({'idea': idea, 'username': username, 'time': datetime.now().isoformat()}) + '\n')

def check_user_registered(username, password):
    if os.path.exists('user_credentials.txt'):
        with open('user_credentials.txt', 'r') as file:
            for line in file:
                registered_username, registered_password = line.strip().split(',')
                if username == registered_username and password == registered_password:
                    return True
    return False

# 装饰器，用于检查用户是否已登录
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 首页路由
@app.route('/')
def home():
    return redirect(url_for('static', filename='Junction.htm'))

# 注册端点
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if check_user_registered(username, password):
        return "User already registered!"
    else:
        with open('user_credentials.txt', 'a') as file:
            file.write(f'{username},{password}\n')
        return f"Registration Successful for {username}!"

# 登录端点
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if check_user_registered(username, password):
        session['username'] = username
        print("Log in successfully!")
        return jsonify(loggedIn=True)
    else:
        return "Login Failed. User not registered or incorrect credentials."
    
@app.route('/suggestions', methods=['POST'])
@login_required
def submit_suggestion():
    suggestion = request.form['suggestion']
    username = session['username']
    save_idea(suggestion, username)
    return "Suggestion submitted!"
@app.route('/ideas', methods=['GET'])
def get_ideas():
    ideas = []
    with open('ideas.txt', 'r') as file:
        for line in file:
            ideas.append(json.loads(line))
    # 按时间排序
    ideas.sort(key=lambda x: x['time'], reverse=True)
    return jsonify(ideas)
# 活动搜索端点

@app.route('/login/status')
def login_status():
    if 'username' in session:
        return {'loggedIn': True}
    else:
        return {'loggedIn': False}
@app.route('/create_activity', methods=['POST'])
@login_required
def create_activity():
    activity_data = {
        'name': request.form['name'],
        'organizer': request.form['organizer'],
        'date': request.form['date'],
        'location': request.form['location'],
        'scale': request.form['scale'],
        'slogan': request.form['slogan'],
        'description': request.form['description'],
    }
    save_activity(activity_data)
    return "Created!"
@app.route('/search_activities', methods=['GET'])
@login_required
def search_activities():
    keyword = request.args.get('search', '')  # 获取搜索关键词
    activities = []
    with open('activities.txt', 'r') as file:
        for line in file:
            activity = json.loads(line)
            # 确保活动字典中包含 'time' 键
            if 'time' in activity:
                if keyword.lower() in activity['name'].lower() or keyword.lower() in activity['description'].lower():
                    activities.append(activity)
            else:
                # 如果没有 'time' 键，可以记录错误、跳过该项或添加默认时间
                print(f"Skipping activity without time: {activity}")
    activities.sort(key=lambda x: x['time'])  # 确认所有活动都有 'time' 键后进行排序
    return jsonify(activities)



# 登出端点
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
