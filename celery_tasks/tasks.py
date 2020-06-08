# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()

# 创建应该Celery实例
app = Celery('celery_tasks.tasks', broker='redis://192.168.1.104:6379/8')


#
@app.task
def send_register_active_email(to_email, username, token):
    # 发送激活邮件
    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    html_message = '''<h1>{},欢迎你成为天天生鲜注册会员</h1>
                               请点击下面连接激活你的账户<br>
                               <a href="http://127.0.0.1:8000/user/active/{}">
                               http://127.0.0.1:8000/user/active/{}/
                               </a>'''.format(username, token, token)
    sender = settings.EMAIL_FROM
    receuver = [to_email]
    send_mail(subject, message, sender, receuver, html_message=html_message)
