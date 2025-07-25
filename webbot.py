#webbot.py
import math
from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
import os, re, time
import json
import msg_deal as msg
from scrlib.mfile import MFile
import scrlib.mlib as lib
from scrlib.userdb import UserDB
from scrlib.imagedb import ImgDB


app = Flask(__name__)
app.secret_key = 'a6ae45f512419d4a35a725d4d04c9c8a'
__invitekey = 'momotalk'

@app.route('/', methods=['GET','POST'])
def dialog_main():
    session['nowurl'] = url_for('dialog_main')
    username = request.cookies.get('user')
    if not username:
        return redirect(url_for('login'))
    lib.log(f'User Login: {username}')
    if username not in user_history:
        user_history[username] = []

    his = '\n'.join(user_history[username])

    return render_template('dialog.html', username = username, history = his)

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
            response = redirect(session.get('nowurl', url_for('dialog_main')))
            response.set_cookie('user', username, max_age=30 * 24 * 3600)
            return response
        else:
            need_invite = True
            if invitecode:
                if invitecode == __invitekey:
                    if re.match('^[\d\w]+$', username):
                        register(username, password)
                        response = redirect(session.get('nowurl', url_for('dialog_main')))
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
    session['nowurl'] = url_for('getpic')
    username = request.cookies.get('user')
    if not username:
        return redirect(url_for('login'))
    
    show_num = config['pic']['show_num'] or 10 # 一页显示的数量
    page = int(request.args.get('page', 1))
    iMode = int(request.args.get('mode', 0))

    pic_path = 'static/pic/'
    preview_path = 'static/pic/preview/'
    filelist = os.listdir(preview_path)
    piclist = []

    filelist = sorted(filelist, key=lambda x: os.path.getmtime(os.path.join(pic_path, x)), reverse=True)
    i = 0   
    index_start = 0 + (page-1) * show_num #开始,包含
    index_end = index_start + show_num #结束,不包含

    imgdb = ImgDB()
    favorlist = imgdb.getFavorList(username)
    
    for f in filelist:
        abspath = os.path.join(pic_path, f)
        if not os.path.isdir(abspath): 
            if f in favorlist:
                favor = '1'
            else :
                favor = '0'
            if iMode == 0 or favor == '1':
                if i >= index_start and i < index_end:
                    piclist.append((f, favor))
                i += 1
    total_page = math.ceil(i / show_num)
    
    return render_template('piclist.html', all_pic = piclist, total_page = total_page, now_page = page, mode = iMode)

@app.route('/set-favorite', methods=['POST'])
def setFavorImg():
    username = request.cookies.get('user')
    if not username:
        return redirect(url_for('login'))
    
    imgid = request.form['id']
    favorite = request.form['favorite']

    # print(f'SetFavorImg {imgid}  {favorite} {type(favorite)}')
    
    imgdb = ImgDB()
    if (favorite == 'true'):
        imgdb.addFavor(username, imgid)
    else:
        imgdb.delFavor(username, imgid)
    imgdb.getFavorList(username)

    return jsonify({'favorite': favorite})

@app.route('/process_input', methods=['POST'])
def process_input():
    userid = request.cookies.get('user', "default")
    # lib.log(f'userid: {userid}')

    user_input = request.form['user_input']
    user_action = (request.form["user_action"] == 'true')  # 玩家主动或客户端自动
    
    #回复
    bot_reply, nextorder = qm.deal(user_input, userid, user_action)

    if userid not in user_history:
        user_history[userid] = []
    if user_action:
        user_history[userid].append('<div class="message user-message">' + user_input.replace('\n', '<br>') + '</div>')
    user_history[userid].append('<div class="message bot-message">' + bot_reply.replace('\n', '<br>') + '</div>')
    if len(user_history) > 110:
        user_history[userid] = user_history[userid][80:]
    return jsonify({'bot_reply': bot_reply, 'nextorder': nextorder})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    userid = request.cookies.get('user', "default")
    if not userid:
        return
    user_history[userid] = []
    return jsonify({})

@app.route('/cloud', methods=['GET', 'POST'])
def filecloud():
    username = request.cookies.get('user')
    session['nowurl'] = url_for('filecloud')
    if not username:
        return redirect(url_for('login'))
    filelst = fs.getFilelist(username)
    filelst = sorted(filelst, key=lambda x: x['time'], reverse=True)

    return render_template('filecloud.html', files = filelst)

@app.route('/uploadfile', methods=['POST'])
def uploadfile():
    username = request.cookies.get('user')
    if not username:
        return jsonify({'error': 'User not login'})
    
    files = request.files
    if len(files) == 0:
        return jsonify({'error': 'No file part'})
    
    lib.log("Start save file...")
    node1 = time.time()
    i = 0
    for filename in files:
        file = files[filename]
        i += 1
        tmp = time.time()
        res = fs.savefile(file, username)
        if res:
            return jsonify(res)
        cost = time.time() - tmp
        lib.log(f'Save {filename} cost {round(cost, 2)}s')
    cost = time.time() - node1
    lib.log(f'Finish cost {round(cost, 2)}s')
    return jsonify({'message': 'File successfully uploaded'})

@app.route('/deletefile', methods=['POST'])
def deletefile():
    username = request.cookies.get('user')
    if not username:
        return jsonify({'error': 'User not login'})
    
    filename = request.form['filename']
    if fs.deletefile(filename, username):
        return jsonify({'message': 'File successfully deleted'})
    else:
        return jsonify({'error': f'File: {filename} not find'})

def register(user, password):
    user_password[user] = password
    userdb.insert(user, password)


def creatrandomstr(lenth=16):
    import secrets
    # 生成一个长度为16的随机字符串 
    random_key = secrets.token_hex(lenth)
    print(random_key)

if __name__ == '__main__':
    config = json.load(open("config.json", encoding = 'utf-8'))
    qm = msg.Message(config)
    fs = MFile(config)
    userdb = UserDB()
    user_password = {}
    user_history = {}
    for one in userdb.get_all_user():
        user_password[one[0]] = one[1]

    app.run(host='0.0.0.0',port=config['server']['port'])
