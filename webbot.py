#webbot.py
import math
from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
import os, re
import msg_deal as msg
import scrlib.mlib as lib
from scrlib.userdb import UserDB

app = Flask(__name__)
app.secret_key = 'a6ae45f512419d4a35a725d4d04c9c8a'
__invitekey = 'momotalk'

@app.route('/', methods=['GET','POST'])
def dialog_main():
    username = request.cookies.get('user')
    lib.log(f'username: {username}')
    if not username:
        return redirect(url_for('login'))
    return render_template('dialog.html', username = username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    need_invite = False
    username = ""
    if request.method == 'POST':
        username = request.form.get('username')
        invitecode = request.form.get('invitecode')
        password = '111111'
        if username in user_password:
            flash(f'Last Logged in as {username}')
            response = redirect(url_for('dialog_main'))
            response.set_cookie('user', username)
            return response
        else:
            need_invite = True
            if invitecode:
                if invitecode == __invitekey:
                    if re.match('^[\d\w]+$', username):
                        register(username, password)
                        response = redirect(url_for('dialog_main'))
                        response.set_cookie('user', username)
                        return response
                    else:
                        flash('Username can only contain words and digits')
                else:
                    flash(f'Wrong Code')
            else:
                flash(f'Need Invite')
    return render_template('login.html', need_invite = need_invite, inputname=username)

@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.set_cookie('user', '', expires=0)
    return response

@app.route('/pic', methods=['GET'])
def getpic():
    show_num = 5 # 一页显示的数量

    page = int(request.args.get('page', 1))

    pic_path = 'static/pic/'
    filelist = os.listdir(pic_path)
    piclist = []

    filelist = sorted(filelist, key=lambda x: os.path.getmtime(os.path.join(pic_path, x)), reverse=True)
    i = 0   
    index_start = 0 + (page-1) * show_num #开始,包含
    index_end = index_start + show_num #结束,不包含
    for f in filelist:
        abspath = os.path.join(pic_path, f)
        if not os.path.isdir(abspath):
            if i >= index_start and i < index_end:
                piclist.append(f)
            i += 1
    total_page = math.ceil(i / show_num)
    
    return render_template('piclist.html', all_pic = piclist, total_page = total_page, now_page = page)

@app.route('/process_input', methods=['POST'])
def process_input():
    userid = request.cookies.get('user') or "default"
    lib.log(f'userid: {userid}')

    user_input = request.form['user_input']
    
    #回复
    bot_reply = qm.deal(user_input, userid)

    return jsonify({'bot_reply': bot_reply})

def register(user, password):
    user_password[user] = password
    userdb.insert(user, password)


def creatrandomstr(lenth=16):
    import secrets
    # 生成一个长度为16的随机字符串
    random_key = secrets.token_hex(lenth)
    print(random_key)

if __name__ == '__main__':
    qm = msg.Message()
    userdb = UserDB()
    user_password = {}
    for one in userdb.get_all_user():
        user_password[one[0]] = one[1]

    app.run(host='0.0.0.0',port='2333')
