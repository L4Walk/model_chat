from flask import render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from utils.email_utils import generate_verification_token, confirm_verification_token, send_verification_email
import os
from datetime import datetime
from models.database import db, app
from models.model_config import ModelConfig
import time
import json

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # user, admin, superadmin
    email_verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.email_verified:
                flash('请先验证您的邮箱后再登录')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # 生成验证令牌并发送验证邮件
        token = generate_verification_token(email)
        verification_url = url_for('verify_email', token=token, _external=True)
        if send_verification_email(email, verification_url):
            flash('注册成功！请查收验证邮件完成邮箱验证', 'success')
        else:
            flash('注册成功，但发送验证邮件失败，请稍后重试', 'warning')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/model_config')
@login_required
def model_config():
    if current_user.role not in ['admin', 'superadmin']:
        flash('权限不足')
        return redirect(url_for('dashboard'))
    
    # 从数据库获取模型配置
    model_configs = ModelConfig.query.all()
    
    # 模拟统计数据（后续可以从数据库获取实际数据）
    stats = {
        'today_calls': 100,  # 示例数据
        'month_calls': 3000,  # 示例数据
        'total_calls': 10000  # 示例数据
    }
    
    return render_template('model_config.html', model_configs=model_configs, stats=stats)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/verify_email/<token>')
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        flash('验证链接已过期或无效')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('用户不存在')
        return redirect(url_for('login'))
    
    if user.email_verified:
        flash('邮箱已经验证过了')
    else:
        user.email_verified = True
        db.session.commit()
        flash('邮箱验证成功！请登录您的账号', 'success')
    
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if current_user.role != 'superadmin':
        flash('权限不足')
        return redirect(url_for('dashboard'))
    
    # 获取当前对话ID
    chat_id = request.args.get('chat_id')
    
    # 模拟对话历史数据
    chat_history = [
        {'id': 1, 'title': '示例对话1', 'created_at': datetime.now()},
        {'id': 2, 'title': '示例对话2', 'created_at': datetime.now()}
    ]
    
    messages = []
    if chat_id:
        # TODO: 从数据库获取对话消息
        messages = [
            {'role': 'user', 'content': '你好'},
            {'role': 'assistant', 'content': '你好！我是AU大模型助手，很高兴为您服务。'}
        ]
    
    return render_template('chat.html', 
                            chat_history=chat_history,
                            current_chat_id=chat_id,
                            messages=messages)
    if request.method == 'POST':
        user_message = request.form.get('message')
        if user_message:
            messages.append({'role': 'user', 'content': user_message})
            # TODO: 调用模型生成回复
            messages.append({'role': 'assistant', 'content': '这是一个示例回复'})
    
    return render_template('chat.html', messages=messages)







@app.route('/user_management')
@login_required
def user_management():
    if current_user.role != 'superadmin':
        flash('权限不足')
        return redirect(url_for('dashboard'))
    
    # 从数据库获取所有用户
    users = User.query.all()
    return render_template('user_management.html', users=users)

@app.route('/add_model_config', methods=['POST'])
@login_required
def add_model_config():
    if current_user.role not in ['admin', 'superadmin']:
        flash('权限不足')
        return redirect(url_for('dashboard'))
    
    name = request.form.get('name')
    api_url = request.form.get('api_url')
    api_key = request.form.get('api_key')
    model_type = request.form.get('model_type')
    
    if not all([name, api_url, api_key, model_type]):
        flash('请填写所有必填字段')
        return redirect(url_for('model_config'))
    
    model_config = ModelConfig(name=name, api_url=api_url, api_key=api_key, model_type=model_type)
    db.session.add(model_config)
    db.session.commit()
    
    flash('模型配置添加成功')
    return redirect(url_for('model_config'))

@app.route('/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    if current_user.role != 'superadmin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': '无效的请求数据'}), 400
        
    def generate():
        # 模拟流式输出
        response = "你好！我是AU大模型助手。我会一个字一个字地回复你的消息。\n让我们来测试一下流式输出功能。"
        for char in response:
            yield char
            time.sleep(0.05)  # 模拟打字效果
    
    return Response(generate(), mimetype='text/plain')







def init_db():
    with app.app_context():
        db.create_all()
        # Create superadmin if not exists
        if not User.query.filter_by(username='root').first():
            superadmin = User(username='root', email='root@admin.com', role='superadmin', email_verified=True)
            superadmin.set_password('root123')
            db.session.add(superadmin)
            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(port=5011, debug=True)