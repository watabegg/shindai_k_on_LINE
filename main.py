from flask import Flask, render_template, request, abort, jsonify
from flask_bootstrap import Bootstrap
from dotenv import load_dotenv
import requests, os, re, json, pandas
import mysql.connector
from mysql.connector import errorcode
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, UnfollowEvent
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from psycopg2 import sql
from io import BytesIO
from datetime import datetime

load_dotenv()

# LINE botの設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# DATABASE_URL = os.environ['DATABASE_URL'] # PostgreSQLデータベースURLを取得
RENDER_APP_NAME = "shindai_k_on_LINE" 

# Google Sheets APIの設定
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
spread_title = 'Sheet1'
SERVICE_ACCOUNT_FILE  = './shindai-k-on-test-5123543195aa.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
gc = gspread.service_account(SERVICE_ACCOUNT_FILE)
worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(spread_title)

table_name = 'reservation'

app = Flask(__name__)
bootstrap = Bootstrap(app)
# RENDER = "https://{}.onrender.com/".format(RENDER_APP_NAME)

header = {
    "Content_Type": "application/json",
    "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
}

# # データベース接続
# def get_connection():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

def get_connection():
    return mysql.connector.connect(user = 'root',password = '',host = 'localhost', db = 'reservation')

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route('/Source/getid.js')
def getID():
    LIFF_ID = os.environ['LIFF_ID']
    return render_template('Source/getid.js', value = LIFF_ID)

@app.route('/Source/base.js')
def base():
    return render_template('Source/base.js')

@app.route('/time.csv')
def csv():
    return render_template('/time.csv')

# アプリにPOSTがあったときの処理
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@app.route('/booking', methods=['POST'])
def booking():
    today = datetime.today()
    time = pandas.read_csv("./templates/time.csv", header=None).values.tolist() # バグるかも
    data = request.json
    access_token = data['accessToken']
    
    response1 = verifyAccessToken(access_token)
    if response1.status_code != 200:
        print("検証エラー")
        return "Verification error", 400

    response2 = getProfile(access_token)
    if response2.status_code != 200:
        print("プロフィール取得エラー")
        return "Profile retrieval error", 400

    user_id = response2.json().get('userId')
    user_name = response2.json().get('displayName')

    line_message = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": f"予約内容\n日付:{data['day']}\n時間:{time[0][int(data['time'])]}\n予約者:{user_name}\n備考:{data['remark']}\nパスワード:{data['password']}"
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + LINE_CHANNEL_ACCESS_TOKEN
    }

    response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, data=json.dumps(line_message))
    
    if response.status_code == 200:
        return jsonify({"message": "予約が完了しました。"})
    else:
        return jsonify({"error": "予約時にエラーが発生しました。"})

def verifyAccessToken(AccessToken):
    return requests.get(f'https://api.line.me/oauth2/v2.1/verify?access_token={AccessToken}')

def getProfile(AccessToken):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + AccessToken
    }
    return requests.get('https://api.line.me/v2/profile', headers=headers)

# botにメッセージを送ったときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="https://liff.line.me/2003081520-k78eblPv"))
    print("返信完了!!\ntext:", event.message.text)


# アプリの起動
if __name__ == "__main__":
    # with get_connection() as conn:
    #     with conn.cursor() as cur:
    #         table_name = 'booking'
    #         sql_query = """
    #             CREATE TABLE IF NOT EXISTS %s 
    #             (timestamp TIMESTAMP, day DATE, time INT, regist_name CHAR, 
    #             part INT, otherpart TINYINT, remark TEXT, name CHAR, password LONGTEXT, delate TINYINT)
    #         """
    #         cur.execute(sql_query, table_name)

    #         conn.commit()
    
    app.run(debug=True)
### End