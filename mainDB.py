import uuid
import os
import json
from random import randint
from datetime import datetime
from flask import Flask
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import utils
import base64
import re
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
app = Flask(__name__)

# isauth : 0,Error 1,Wait_Veryify 2.SUCC


class MAINDB():
    def __init__(self):
        adminsdk = os.path.join(
            app.root_path, 'firebase-keys/stock-account.json')
        dburl = 'https://stock-account-dfbc2-default-rtdb.firebaseio.com/'
        try:
            cred = credentials.Certificate(adminsdk)
            firebase_admin.initialize_app(cred, {'databaseURL': dburl})
        except:
            pass
        self.ref = db.reference()

    def telop_init(self):

        ref_child = self.ref.child('Global_Setting')
        ref_child.set({
            'need_verify': True,
            'open_signup': True
        })

        self.ref.child('users').set({})
        self.ref.child('passbook').set({})
        self.ref.child('inventory').set({})
        self.ref.child('orders').set({})
        self.ref.child('profitloss').set({})

    # user_name,user_token, isauth, msg = mainDB.Signin(account, password)

    def Signin(self, account, password):
        setting = self.get_any_list("Global_Setting")
        getuser = self.get_any_list("users/{}".format(base64.b64encode(
            account.encode('UTF-8')).decode('UTF-8')))
        print(getuser)
        if getuser == {}:
            return "", "", 0, "帳號或密碼錯誤"

        if getuser['password'] != password:
            return "", "", 0, "帳號或密碼錯誤"

        if getuser['if_verify'] == False and setting['need_verify']:
            return getuser['name'], "", 1, "需要驗證"

        return getuser['name'], getuser['token'], 2, "成功", getuser['role']

    # user_name,user_token, isauth, msg = mainDB.Singup(new_account, new_password)

    def Signup(self, new_account, new_password, role):
        setting = self.get_any_list("Global_Setting")
        base64ed_acc = base64.b64encode(
            new_account.encode('UTF-8')).decode('UTF-8')

        print(setting)
        userlist = self.get_any_list("users")
        print("資料庫操作：註冊")
        if setting['open_signup']:
            if (new_account == "") or (new_password == ""):
                return "", "", 0, "輸入不得為空"
            if base64ed_acc in userlist:
                return "", "", 0, "此Email已被註冊"
            if re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', new_account) == None:
                return "", "", 0, "請輸入一個有效的Email帳號"

            name = utils.getrandom(30)
            token = utils.getrandom(50)
            ref_newUSER = self.ref.child(
                'users/{}'.format(base64ed_acc))

            ref_newUSER.set({
                'name': name,
                'token': token,
                'password': new_password,
                'if_verify': False,
                'role': role
            })

            self.addpassbook(token, 300000, 300000, "系統存入", "開戶預設", 0)

            if setting['need_verify']:
                self.activation_mail(new_account)
                return name, "", 1, "請至Email查看驗證信", role
            else:
                return name, token, 2, "成功", role

        else:
            return "", "", 0, "現階段不開放註冊新用戶", role

    def addpassbook(self, token, balance, deposit, memo, remarks, withdrawal):
        now = datetime.now()

        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        ref_PASSBOOK = self.ref.child(
            'passbook/{}/{}'.format(token, dt_string))
        ref_PASSBOOK.set({
            "balance": balance,  # 餘額 (float)
            "date": now.strftime("%Y-%m-%d"),  # 日期 (str)
            "deposit": deposit,  # 存款 (float)
            "memo": memo,  # 備註 (str)
            "remarks": remarks,  # 備註 (str)
            "withdrawal": withdrawal  # 提款 (float)
        })

    def addorders(self, token, amount, enc_action, ent_num, sprice, stitle, stockid):
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        ref_ORDERS = self.ref.child(
            'orders/{}/{}'.format(token, dt_string))
        ref_ORDERS.set({
            "amount": amount,  # 價格 (+/-)
            "enc_action": enc_action,  # 買賣 (buy/sell)
            'ent_num': ent_num,  # 數量 (int)
            'spice': sprice,  # 股票價格 (float)
            'stitle': stitle,  # 股票名稱 (str)
            "stockid": stockid  # 股票代號 (str)
        })

    def updateinventory(self, token, stockid, amount, mcost):
        ref_INVENTORY = self.ref.child(
            'inventory/{}/{}'.format(token, stockid))
        ref_INVENTORY.set({
            "amount": amount,  # 數量 (int)
            'mean_cost': mcost,  # 平均成本 (float)
        })

    def getinventory(self, token):
        ref_inventory = self.ref.child(
            'inventory/{}'.format(token))
        if ref_inventory.get() == None:
            return {}
        return ref_inventory.get()

    def buy(self, token, stockid, amount, price):
        inventory = self.getinventory(token)
        stockid = stockid.replace(".", "&*&")
        if stockid in inventory:
            newamount = int(inventory[stockid]['amount']) + int(amount)
            newmcost = (float(inventory[stockid]['mean_cost']) *
                        int(inventory[stockid]['amount']) + float(price) * int(amount)) / newamount
            newmcost = round(newmcost, 2)
            self.updateinventory(token, stockid, newamount, newmcost)
        else:
            self.updateinventory(token, stockid, amount, price)

        self.addorders(token, amount, "buy", stockid, price, "買入", stockid)

    def sell(self, token, stockid, amount, price):
        inventory = self.getinventory(token)
        stockid = stockid.replace(".", "&*&")
        if stockid in inventory:
            newamount = inventory[stockid]['amount'] - amount
            newmcost = inventory[stockid]['mean_cost']
            if newamount == 0:
                self.delemptyinventory(token, stockid)
            self.updateinventory(token, stockid, newamount, newmcost)
        else:
            self.updateinventory(token, stockid, amount, price)

        self.addorders(token, amount, "sell", stockid, price, "賣出", stockid)

    def delemptyinventory(self, token, stockid):
        inventory = self.getinventory(token)
        stockid = stockid.replace(".", "&*&")
        if stockid in inventory:
            self.ref.child(
                'inventory/{}/{}'.format(token, stockid)).delete()

    def activation_mail(self, email):
        userlist = self.get_any_list("users")
        if base64.b64encode(email.encode('UTF-8')).decode('UTF-8') in userlist:
            s = Serializer(current_app.config['SECRET_KEY'], 1800)
            semail = s.dumps(
                {'user_email': email, 'mode': "verify"}).decode("UTF-8")
            emailsub = f"""<center><table align="center" cellspacing="0" cellpadding="0" width="100%"><tr><td align="center" style="padding:10px"><table border="0" class="mobile-button" cellspacing="0" cellpadding="0"><tr><td align="center" bgcolor="#2b3138" style="background-color:#2b3138;margin:auto;max-width:600px;-webkit-border-radius:5px;-moz-border-radius:5px;border-radius:5px;padding:15px 20px" width="100%"><!--[if mso]>&nbsp;<![endif]--> <a href="{current_app.config['NOW_URL']}/stockVerify/{semail}" target="_blank" style="color:#fff;font-weight:400;text-align:center;background-color:#2b3138;text-decoration:none;border:none;-webkit-border-radius:5px;-moz-border-radius:5px;border-radius:5px;display:inline-block"><span style="font-size:16px;font-family:Helvetica,Arial,sans-serif;color:#fff;font-weight:400;line-height:1.5em;text-align:center">點此驗證</span> </a><!--[if mso]>&nbsp;<![endif]--></td></tr></table></td></tr></table></center>"""
            utils.send_email("驗證信", emailsub, email)
            return "帳號驗證信發送成功，請至Email信箱查看"
        return "找不到此用戶"

    def reset_mail(self, email):
        userlist = self.get_any_list("users")
        if base64.b64encode(email.encode('UTF-8')).decode('UTF-8') in userlist:
            s = Serializer(current_app.config['SECRET_KEY'], 1800)
            semail = s.dumps(
                {'user_email': email, 'mode': "resetpassword"}).decode("UTF-8")
            emailsub = f"""<center><table align="center" cellspacing="0" cellpadding="0" width="100%"><tr><td align="center" style="padding:10px"><table border="0" class="mobile-button" cellspacing="0" cellpadding="0"><tr><td align="center" bgcolor="#2b3138" style="background-color:#2b3138;margin:auto;max-width:600px;-webkit-border-radius:5px;-moz-border-radius:5px;border-radius:5px;padding:15px 20px" width="100%"><!--[if mso]>&nbsp;<![endif]--> <a href="{current_app.config['NOW_URL']}/stockResetPassword/{semail}" target="_blank" style="color:#fff;font-weight:400;text-align:center;background-color:#2b3138;text-decoration:none;border:none;-webkit-border-radius:5px;-moz-border-radius:5px;border-radius:5px;display:inline-block"><span style="font-size:16px;font-family:Helvetica,Arial,sans-serif;color:#fff;font-weight:400;line-height:1.5em;text-align:center">點此驗證</span> </a><!--[if mso]>&nbsp;<![endif]--></td></tr></table></td></tr></table></center>"""
            utils.send_email("驗證信", emailsub, email)
            return "重設密碼驗證信發送成功，請至Email信箱查看"
        return "找不到此用戶"

    def verify(self, email):
        try:
            s = Serializer(current_app.config['SECRET_KEY'])
            data = s.loads(email.encode("UTF-8"))
            if data['mode'] == 'verify':
                ref_child = self.ref.child("users/{}".format(base64.b64encode(
                    data['user_email'].encode('UTF-8')).decode('UTF-8')))
                getuser = self.get_any_list("users/{}".format(base64.b64encode(
                    data['user_email'].encode('UTF-8')).decode('UTF-8')))
                getuser["if_verify"] = True
                ref_child.set(getuser)
                return "驗證成功，5秒後返回登入畫面", ""
            else:
                return "", "無效的連結"
        except Exception as e:

            return "", "無效的連結"

    def resetpass(self, email, password=None):
        try:
            s = Serializer(current_app.config['SECRET_KEY'])
            data = s.loads(email.encode("UTF-8"))
            if data['mode'] == 'resetpassword':
                ref_child = self.ref.child("users/{}".format(base64.b64encode(
                    data['user_email'].encode('UTF-8')).decode('UTF-8')))
                getuser = self.get_any_list("users/{}".format(base64.b64encode(
                    data['user_email'].encode('UTF-8')).decode('UTF-8')))

                if password == None:
                    return "", ""
                else:
                    getuser["password"] = password
                    ref_child.set(getuser)
                    return "密碼更改成功", ""
            else:
                return "", "無效的連結"
        except Exception as e:
            return "", "無效的連結"

    def get_any_list(self, get):
        ref_child = self.ref.child(get)
        jsondata = ref_child.get()
        if isinstance(jsondata, dict) or isinstance(jsondata, list):
            return jsondata
        else:
            return {}

    def testsetauser(self):
        ref_child = self.ref.child(
            'users/{}'.format(utils.getrandom(30)))
        ref_child.set({
            'name': utils.getrandom(30),

        })

    def testchange(self):
        ref_child = self.ref.child('Global_Setting')
        get = dict(self.get_any_list())
        get["need_verify"] = "N"

        ref_child.set(get)

    def getpassbook(self, token):
        return self.get_any_list(f"passbook/{token}")

    def listalluser(self):
        return self.get_any_list("users")


if __name__ == "__main__":
    mainDB = MAINDB()
    inp = int(input(
        "0.取消 1.還原 2.測試新用戶 3.測試更改設定 4.取得測試 5.列出所有用戶 6.getinventory 7.updateinventory : "))
    if inp == 1:
        mainDB.telop_init()
    elif inp == 2:
        mainDB.testsetauser()
    elif inp == 3:
        mainDB.testchange()
    elif inp == 4:
        inp = input(": ")
        print(mainDB.get_any_list(inp))
    elif inp == 5:
        print(mainDB.listalluser())
    elif inp == 6:
        print(mainDB.getinventory(
            "0b4087106c662ac11a07cf91a84e29cc4c090cc49e84fdd7c0"))
    elif inp == 7:
        print(mainDB.updateinventory(
            "0b4087106c662ac11a07cf91a84e29cc4c090cc49e84fdd7c0", "2303&*&TW", 1, 5))
