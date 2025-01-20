from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///au_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 邮件服务器配置
app.config['MAIL_SERVER'] = 'smtp.feishu.cn'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'AI@agent-universe.cn'
app.config['MAIL_PASSWORD'] = '2kLjUIlb7FSHaAta'
app.config['MAIL_USE_TLS'] = True

db = SQLAlchemy(app)