import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification-salt')

def confirm_verification_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification-salt', max_age=expiration)
        return email
    except:
        return False

def send_verification_email(to_email, verification_url):
    smtp_server = current_app.config['MAIL_SERVER']
    smtp_port = current_app.config['MAIL_PORT']
    smtp_username = current_app.config['MAIL_USERNAME']
    smtp_password = current_app.config['MAIL_PASSWORD']

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = 'AU大模型平台 - 邮箱验证'

    body = f'''
    <html>
        <body>
            <p>您好！</p>
            <p>感谢您注册 AU大模型平台。请点击以下链接验证您的邮箱：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>此链接有效期为1小时。如果您没有注册我们的平台，请忽略此邮件。</p>
            <p>祝您使用愉快！</p>
            <p>AU大模型平台团队</p>
        </body>
    </html>
    '''

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f'发送邮件失败: {str(e)}')
        return False