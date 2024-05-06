import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()


class EmailSender:
    def __init__(self):
        self.sender = os.getenv("EMAIL")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.smtp_port = os.getenv("EMAIL_PORT")
        self.message = MIMEMultipart()
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.template = Environment(loader=FileSystemLoader('template'))
        self.server = None
        self.bcc = os.getenv("EMAIL_BCC")

    def get_success_body(self, username, password, date, card, count):
        template = self.template.get_template('success.html')
        rendered_template = template.render(
            title='邮件标题',
            username=username,
            date=date,
            card=card,
            count=count,
            password=password
        )
        return rendered_template

    def get_morning_success_body(self, username, password):
        template = self.template.get_template('success.html')
        rendered_template = template.render(
            title='邮件标题',
            username=username,
            password=password
        )
        return rendered_template

    def send_msg(self, subject, emails, body):
        self.message['From'] = formataddr((Header('订票软件', 'utf-8').encode(), self.sender))
        self.message['To'] = formataddr((Header('收件人名称', 'utf-8').encode(), ', '.join(emails)))
        self.message['Bcc'] = formataddr((Header('收件人名称', 'utf-8').encode(), self.bcc))
        self.message['Subject'] = Header(subject, 'utf-8')
        html_part = MIMEText(body, 'html', 'utf-8')
        self.message.attach(html_part)
        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.server.login(self.sender, self.password)
            self.server.sendmail(self.sender, emails, self.message.as_string())
            print('邮件发送成功')
        except Exception as e:
            print('邮件发送失败:', e)
        finally:
            self.server.quit()


if __name__ == '__main__':
    email = EmailSender()
    email.send_msg('你有新的订单', ['35617949@qq.com'], email.get_success_body(username='张三', password="xxxx", date='2021-10-01', card='123456', count=2))
