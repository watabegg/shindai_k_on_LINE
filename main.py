from flask import Flask, render_template, request, abort, jsonify
from dotenv import load_dotenv
import requests, os, re, json, pandas, textwrap
import mysql.connector as db
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
# import psycopg2 as db
from io import BytesIO
from datetime import datetime, timedelta, timezone
import functions

JST = timezone(timedelta(hours=+9), 'JST')

load_dotenv()

# LINE botの設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# DATABASE_URL = os.environ['DATABASE_URL'] # PostgreSQLデータベースURLを取得
RENDER_APP_NAME = "shindai_k_on_LINE" 

# ローカルでのMySQL設定
config_file = 'database_config.json'

with open(config_file, 'r') as f:
    config = json.load(f)

table_name = 'reservation'

app = Flask(__name__)
# RENDER = "https://{}.onrender.com/".format(RENDER_APP_NAME)

header = {
    "Content_Type": "application/json",
    "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
}

# # データベース接続
# def get_connection():
#     return psycopg2.connect(DATABASE_URL, sslmode="require")

def get_connection():
    return db.connect(**config)

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

@app.route('/part.csv')
def part():
    return render_template('/part.csv')

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

    part_prd = functions.part_prd(data['part'])

    part_str = functions.part_str(data['part'])

    other_list = ['なし','あり']

    line_message = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": textwrap.dedent(f"""\
                    予約内容
                    タイムスタンプ:{data['timestamp']}
                    日付:{data['day']}
                    時間:{time[0][int(data['time'])]}
                    登録名:{data['regist_name']}
                    パート:{part_str}
                    他パート参加:{other_list[int(data['otherpart'])]}
                    予約者:{user_name}
                    備考:{data['remark']}
                    パスワード:{data['password']}""")
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + LINE_CHANNEL_ACCESS_TOKEN
    }

    try:
        response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, data=json.dumps(line_message))

        with get_connection() as conn:
            with conn.cursor() as cur:
                table_name = 'booking'
                sql_query = f"""
                            INSERT INTO {table_name} (timestamp, day, time, regist_name, part, otherpart, remark, name, password)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql_query, (datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S'),datetime.strptime(data['day'], '%Y-%m-%d'),int(data['time']),data['regist_name'],part_prd,int(data['otherpart']),data['remark'],user_name,data['password']))
                conn.commit()

        return "予約が完了しました。"

    except requests.RequestException as e:
        print(f"リクエストエラーが発生しました:{e}")
        return "リクエストエラーが発生しました", 500

    except db.Error as e:
        print(f"データベースエラーが発生しました:{e}")
        return "データベースエラーが発生しました", 500


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
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                table_name = 'booking'
                sql_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} 
                    (
                        timestamp TIMESTAMP, day DATE, time INT, regist_name CHAR, 
                        part INT, otherpart TINYINT, remark TEXT, name CHAR, password LONGTEXT, delate TINYINT
                    ) DEFAULT CHARSET=utf8
                """
                cur.execute(sql_query)

                conn.commit()
    except db.Error as e:
        print(f'エラーが発生しました:{e}')
    
    finally:
        if conn.is_connected():
            conn.close()
    
    app.run(debug=True)
### End