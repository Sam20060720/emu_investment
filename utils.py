import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import random


app_host = 'http://localhost:5000'
if 'DYNO' in os.environ:
    app_host = 'https://flaskpyone.herokuapp.com'


def send_email(subject, embody, recipient='sam20060720@gmail.com'):
    # flaskemail of google account
    sender = 'sam200607205@gmail.com'
    password = 'ptmxadfeaeapitkv'
    # email
    content = MIMEMultipart()
    content['subject'] = subject
    content['from'] = sender
    content['to'] = recipient
    # content.attach(MIMEText('主機時間'))
    content.attach(MIMEText(embody, 'html'))

    with smtplib.SMTP(host='smtp.gmail.com', port='587') as smtp:
        try:
            # 驗證 SMTP 伺服器
            smtp.ehlo()
            # 建立加密傳輸
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(content)
        except Exception as e:
            pass


def get_now():
    import pytz
    from datetime import datetime
    taipei = pytz.timezone('Asia/Taipei')
    now = datetime.now(taipei)
    return now


def get_datetime():
    now = get_now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def get_nowid():
    now = get_now()
    return now.strftime("%y%m%d%H%M")


def get_sha2(stext, opt=2):
    import hashlib
    sha2 = '256'
    if opt == 2:
        sha2 = '384'
    elif opt == 3:
        sha2 = '512'
    return eval(f"hashlib.sha{sha2}(stext.encode('utf8')).hexdigest()")


def getrandom(size=128):
    temp = str(random.randint(111, 999)) + \
        str(random.randint(111, 999)) + str(random.randint(111, 999))

    return get_sha2(temp, 3)[0: size]


if __name__ == '__main__':
    print('datetime:', get_datetime())
    print('nowid:', get_nowid())
    while True:
        print('a. Get SHA-2 Hash')
        print('b. Test Gmail')
        print('c. Random Text')
        print('q. Quit')
        op = input('> ').lower()
        if op == 'q':
            break
        elif op == 'a':
            while True:
                stext = input('Input a text to get SHA-2 hash (q. Quit): ')
                if stext.lower() in ('q', 'quit'):
                    break
                else:
                    opt = input('1.SHA-256  2.SHA-384  3.SHA-512: ')[0]
                    if opt in '123':
                        print(get_sha2(stext, int(opt)))
                        print()
        elif op == 'b':
            while True:
                embody = input('Input email body (q. Quit): ')
                if embody.lower() in ('q', 'quit'):
                    break
                else:
                    subject = f'Email Test ({get_now()})'
                    send_email(subject, embody)
        elif op == 'c':
            print(getrandom(int(input("Size (<128): "))))
        print()
