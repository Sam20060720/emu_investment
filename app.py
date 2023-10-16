import utils
from werkzeug.local import LocalProxy
from functools import wraps
from datetime import date, timedelta
import json
import os
from flask import Flask, render_template, send_from_directory, session, request, redirect, url_for, current_app, jsonify
import finance

from mainDB import MAINDB
mainDB = MAINDB()

app = Flask(__name__)
log = LocalProxy(lambda: current_app.logger)
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
# SHA-256 from 'flaskblank'
app.config['SECRET_KEY'] = 'ad4daf864b7ef595f5bbb6d1d55aca53c4e1c959827327e91ab15478b5164d9a'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['NOW_URL'] = 'http://127.0.0.1:8000'
cyear = date.today().year
def nowid(): return utils.get_nowid()
def dtnow(): return utils.get_datetime()


@app.before_request
def before_request():
    if 'DYNO' in os.environ:
        if request.url.startswith('http://'):
            url = request.url.replace('http://', 'https://', 1)
            code = 301
            return redirect(url, code=code)


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if session.get('is_auth') is None:
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function


def login_required_stock(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        print(f"is auth : {session.get('is_auth')}")
        if session.get('is_auth') is None:
            return redirect(url_for('stockLogin'))
        return func(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect(url_for('stock'))


@app.route('/stock', methods=['GET', 'POST'])
@login_required_stock
def stock():
    return render_template("/stock/stock-assets.html")


@app.route('/stockLogin', methods=['GET', 'POST'])
def stockLogin():
    vaild_inputs = ['act_code', 'newAccount', 'newPassword',
                    'theAccount', 'txtAccount', 'txtPassword']
    act_code = ''
    submit_result = ''
    if request.method == "POST":
        form_inputs = sorted(list(request.form.keys()))
        if form_inputs == vaild_inputs:
            act_code = request.form.get('act_code')
            account = request.form.get('txtAccount')
            password = request.form.get('txtPassword')
            new_account = request.form.get('newAccount')
            new_password = request.form.get('newPassword')
            the_account = request.form.get('theAccount')
            if act_code == "Signin":
                user_name, user_token, isauth, msg, role = mainDB.Signin(
                    account, password)
                submit_result = msg
                if isauth == 1:
                    act_code = "Resend"
                elif isauth == 2:
                    session['is_auth'] = True
                    session['role_name'] = role
                    session['view_name'] = user_name
                    session['user_token'] = user_token
                    session['account'] = account
                    session['portal'] = 'stock'
                    return redirect(url_for("stock"))

            elif act_code == "Signup":
                user_name, user_token, isauth, msg, role = mainDB.Signup(
                    new_account, new_password, "user")
                print("run Signup")
                submit_result = msg
                if isauth == 1:
                    act_code = "Signin"
                elif isauth == 2:
                    session['is_auth'] = True
                    session['role_name'] = role
                    session['view_name'] = user_name
                    session['user_token'] = user_token
                    session['account'] = account
                    session['portal'] = 'stock'
                    return redirect(url_for("stock"))

            elif act_code == "ResendPassword":
                msg = mainDB.reset_mail(the_account)
            elif act_code == "ResendActivation":
                msg = mainDB.activation_mail(the_account)
            try:
                if session['is_auth'] == 2:
                    return redirect(url_for("stock_ai"))
                else:
                    submit_result = msg
            except:
                submit_result = msg
        else:
            return redirect(url_for('denied'))
        return render_template("/stock/login-stock.html", account=account, new_account=new_account, submit_result=submit_result, act_code=act_code, cyear=cyear, nowid=nowid)
    print(act_code)
    return render_template("/stock/login-stock.html", submit_result=submit_result, act_code=act_code, cyear=cyear, nowid=nowid)


@app.route('/stockVerify/<token>', methods=['GET', 'POST'])
def stock_verify(token):
    verify_suc, verify_fail = mainDB.verify(token)
    return render_template("/stock/verify-stock.html", verify_suc=verify_suc, verify_fail=verify_fail, cyear=cyear, nowid=nowid)


@app.route('/stockResetPassword/<token>', methods=['GET', 'POST'])
def stock_ResetPassword(token):
    verify_suc, verify_fail = mainDB.resetpass(token)
    if request.method == "POST":
        if sorted(list(request.form.keys())) != ['newPassword']:
            return redirect(url_for('denied'))
        new_password = request.form.get('newPassword')
        verify_suc, verify_fail = mainDB.resetpass(token, new_password)

    return render_template("/stock/password-stock.html", token=token, verify_suc=verify_suc, verify_fail=verify_fail, cyear=cyear, nowid=nowid)


@app.route('/stock-assets', methods=['GET', 'POST'])
@login_required
def stock_assets():
    return render_template("/stock/stock-assets.html", nowid=nowid)


@app.route("/stockPassbook", methods=["GET", "POST"])
@login_required
def stock_passbook():
    return {"passbook": mainDB.getpassbook(session['user_token'])}


@app.route("/stock/inventory_list", methods=["GET", "POST"])
@login_required
def stock_listinventory():
    userinventory = mainDB.getinventory(session['user_token'])
    adict = []
    # {"inventory":{"2303":{"inv_num":1,"mcost":"52.90","name":"\u806f\u96fb","profitloss":"-500","roi":"-0.95%","sprice":"52.40","stockex":"2303:TPE"}}}
    print(userinventory)
    for i in userinventory:
        reali = i.replace("&*&", ".")
        adict.append({
            "stockex": reali,
            "inv_num": userinventory[i]['amount'],
            "mcost": userinventory[i]['mean_cost'],
            "currency": userinventory[i].get('currency') or "NTD",
            'profitloss': '',
            # 'sprice': stockinfo['price'],
        })

    return {"inventory": adict}


@app.route("/stock-entrust", methods=["GET"])
@login_required
def stock_entrust():
    return render_template("/stock/stock-entrust.html", nowid=nowid)


@app.route("/search_stock", methods=["POST"])
@login_required
def search_stock():
    stock = request.form.get('stock')
    stockinfo = finance.search(stock)
    stockinfo = list(set(stockinfo))
    try:
        stockinfo.remove("PRIVATE")
    except:
        pass
    return jsonify(stockinfo)


@app.route("/stock_info", methods=["POST"])
@login_required
def stock_info():
    stock = request.form.get('stock')
    intenvel = request.form.get('intenvel') or "1m"
    timerange = request.form.get('timerange') or "1d"

    stockinfo = finance.getinfo(stock, timerange, intenvel)
    return jsonify(stockinfo)


@app.route("/stock/buy", methods=["POST"])
@login_required
def stock_buy():
    stock = request.form.get('stock')
    price = request.form.get('price')
    amount = request.form.get('amount')
    buy = mainDB.buy(session['user_token'], stock, amount, price)
    return jsonify(buy)


@app.route("/stock/sell", methods=["POST"])
@login_required
def stock_sell():
    stock = request.form.get('stock')
    price = float(request.form.get('price'))
    amount = int(request.form.get('amount'))
    sell = mainDB.sell(session['user_token'], stock, amount, price)
    return jsonify(sell)


@app.route("/getrate", methods=["POST"])
@login_required
def getrate():
    fromex = request.form.get('fromex')
    toex = request.form.get('toex')
    price = request.form.get('price')
    price = float(price)
    rate = finance.getrate(fromex, toex, price)
    return jsonify({"price": rate})


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/denied')
def denied():
    return render_template("denied.html", cyear=cyear, nowid=nowid())


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html", cyear=cyear, nowid=nowid()), 404


if __name__ == '__main__':
    # bot_forweb.loop.create_task(app.run_task(host="0.0.0.0", port=8000))
    # bot_forweb.run(DISCORD_BOT_FORWEB_TOKEN)
    app.run(host="0.0.0.0", port=8000, debug=True)
