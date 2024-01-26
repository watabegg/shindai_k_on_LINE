from flask import Flask, render_template, request, abort
import requests, os, re
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, UnfollowEvent
import psycopg2
from psycopg2 import sql
from datetime import datetime


# LINE botの設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

DATABASE_URL = os.environ['DATABASE_URL'] # PostgreSQLデータベースURLを取得
RENDER_APP_NAME = "shindai_k_on_LINE" 

today = datetime.datetime.today()
time =['7:30~9:00','9:00~10:30','10:40~12:10','12:10~13:00','13:00~14:30','14:40~16:10','16:20~17:50','18:00~19:30','19:30~21:00']

table_name = 'reservation'
flag = 0

app = Flask(__name__)
RENDER = "https://{}.onrender.com/".format(RENDER_APP_NAME)

header = {
    "Content_Type": "application/json",
    "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN
}

# データベース接続
def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# データをデータベースに挿入
def insert_data(table_name, value):
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = sql.SQL("INSERT INTO {} (date, location, purpose, amount) VALUES (%s, %s, %s, %s)").format(
                sql.Identifier(table_name)
                )
            cur.execute(query, value)

            conn.commit()

# ユーザごとの月の合計金額取得関数
def get_monthly_total(user_id):
    today = datetime.date.today()
    start_of_month = today.replace(day=1)
    end_of_month = today.replace(day=1, month=today.month+1) - datetime.timedelta(days=1)

    with get_connection() as conn:
        with conn.cursor() as cur:
            # user_idをテーブル名とする
            table_name = user_id
            # 月の合計金額を取得するSQLクエリ
            query = sql.SQL("SELECT SUM(amount) FROM {} WHERE date BETWEEN %s AND %s").format(
                sql.Identifier(table_name)
            )
            cur.execute(query, [start_of_month, end_of_month])
            total_amount = cur.fetchone()[0]
            return total_amount

# メッセージ送信のための関数
def message_reply(event, message): 
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )

# 予約のための関数
def rsv_main(event):
    exit_flag = 0
    while True:
        message_reply(event, "予約を開始します。部室予約を中止する場合は「中止」と入力してください.")
        
        while True:
            text = event.message.text.lower()

            if text == '中止':
                exit_flag = 1
                break

            message_reply(event, "予約する日をYYYY/MM/DDで教えてください\n例)2024/01/25")
            res = re.match('20[0-9]{2}/[0-9]+/[0-9]{2}', text)

            if res:
                date = datetime.strptime(text, '%Y/%m/%d')
                if today > date:
                    message_reply(event, "入力エラー:今日より前の日付が入力されています。")
                else:
                    message_reply(event, f"{date}で予約をします。")
                    break
            else:
                message_reply(event, "入力エラー:2024/01/25のようなフォーマットで教えてください。")

        if exit_flag == 1:
            message_reply(event, "予約が中止されました。")
            break

        while True:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    query = sql.SQL("SELECT time FROM {} WHERE day = %s").format(
                        sql.Identifier(table_name)
                    )
                    cur.execute(query, date)
                    day_time = cur.fetchall()
                    time_messege = ''
                    for i in day_time:
                        time_messege += f'{i+1}:{time[i]}\n'
                    message_reply(event, f"{date}で予約出来る時間は\n{time_messege}です。")
                    message_reply(event, f"予約する日を時間を一桁の数字で教えてください。\n{time[0]}を取るときの例)1")

                    text = event.message.text.lower()

                    if text == '中止':
                        exit_flag = 1
                        break

                    res = re.match('[0-9]', text)

                    if res:
                        input_time = int(text) - 1
                        if input_time in day_time:
                            message_reply(event, "入力エラー:その時間は予約不可能です。")
                        else:
                            message_reply(event, f"{time[input_time]}で予約をします。")
                            break
                    else:
                        message_reply(event, "入力エラー:想定外の入力です。入力は一桁の数字でお願いします。")

        if exit_flag == 1:
            message_reply(event, "予約が中止されました。")
            break

        while True:
            message_reply(event, "使用する形態を入力してください。例)バンド練")

            text = event.message.text.lower()

            if text == '中止':
                exit_flag = 1
                break
            



# カレンダーを表示させる
@app.route("/") 
def hello_world():
    return "hello world!"


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


# botにメッセージを送ったときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.lower()
    profile = line_bot_api.get_profile(event.source.user_id)

    if flag == 0: # default
        if text == '予約':
            flag = 1 
        elif text == '予約確認':
            flag = 2
    elif flag == 1: # 予約がポストされた時の処理
        rsv_main(event)
    elif flag == 2: # 予約確認がポストされた時の処理
        a=1
    elif flag == 3: # 予約削除がポストされた時の処理
        a=1
    elif flag == 4: # 予約訂正がポストされた時の処理
        a=1
    else: # その他のポスト処理(例外処理)
        a=1

    

# # botがフォローされたときの処理
# @handler.add(FollowEvent)
# def handle_follow(event):
#     profile = line_bot_api.get_profile(event.source.user_id)
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             conn.autocommit = True
#             # user_idをテーブル名とする
#             table_name = profile.user_id
#             # テーブルが存在しない場合のみ作成
#             cur.execute(sql.SQL("CREATE TABLE IF NOT EXISTS {} (date DATE, location VARCHAR, purpose VARCHAR, amount INT)").format(
#                 sql.Identifier(table_name)
#             ))
#             conn.commit()


# # botがアンフォロー(ブロック)されたときの処理
# @handler.add(UnfollowEvent)
# def handle_unfollow(event):
#     profile = line_bot_api.get_profile(event.source.user_id)
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             conn.autocommit = True
#             cur.execute('DROP TABLE IF EXISTS %s', profile.user_id)
#     print("userIdの削除OK!!")


# アプリの起動
if __name__ == "__main__":

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
### End