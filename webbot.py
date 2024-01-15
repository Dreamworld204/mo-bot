#webbot.py
from flask import Flask, render_template, request, jsonify, session
import os
import msg_deal as msg
import mlib as lib

app = Flask(__name__)
app.secret_key = 'a6ae45f512419d4a35a725d4d04c9c8a'

@app.route('/',methods=['GET','POST'])
def dialog_main():
    return render_template('dialog.html')

session_num = 0
@app.route('/process_input', methods=['POST'])
def process_input():
    user_input = request.form['user_input']
    global session_num

    sessionid = session.get('session_id')
    if not sessionid:
        session_num += 1
        session['session_id'] = session_num
        sessionid = session_num
    
    #回复
    bot_reply = qm.deal(user_input, sessionid)

    return jsonify({'bot_reply': bot_reply})

def creatrandomstr(lenth=16):
    import secrets
    # 生成一个长度为16的随机字符串
    random_key = secrets.token_hex(lenth)
    print(random_key)

if __name__ == '__main__':
    qm = msg.Message()

    app.run(host='0.0.0.0',port='2333')
