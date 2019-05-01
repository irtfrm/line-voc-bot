import os
import sys
from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    line_id = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

class RepSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry = db.Column(db.String(80), nullable=False)
    flag = db.Column(db.Boolean)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
        backref=db.backref('rep_settings', lazy=True))

    def __repr__(self):
        return '<RepSetting %r>' % (str(self.user_id) + ':' + self.entry)

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(120), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User',
        backref=db.backref('words', lazy=True))

    def __init__(self, word, user_id):
        self.word = word
        self.user_id = user_id
    
    def __repr__(self):
        return '<Word %r>' % self.word

# 環境変数からchannel_secret・channel_access_tokenを取得
channel_secret = os.environ['CHANNEL_SECRET']
channel_access_token = os.environ['CHANNEL_ACCESS_TOKEN']


if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def hello_world():
    #reg = User(name, email)
    #db.session.add(reg)
    #db.session.commit()
    return 'Hello World!'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    line_id = event.source.user_id
    profile = line_bot_api.get_profile(line_id)

    u = User.query.filter_by(line_id=line_id).first()
    if u == None:
        u = User(username=profile.display_name, line_id=line_id)
        db.session.add(u)
        db.session.commit()

    if text == "単語登録":

        word_registration = RepSetting(entry='word_registration',user=u)
        db.session.add(word_registration)
        db.session.commit()

        line_bot_api.reply_message(
           event.reply_token,
            TextSendMessage(text="登録したい単語を教えてね！"))
    else:
#        if voc_add:
#            voc_add = False
#            voc_list.append(text)
#            line_bot_api.reply_message(
#                event.reply_token,
#                TextSendMessage(text=text + "を追加しました！"))
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    app.run()