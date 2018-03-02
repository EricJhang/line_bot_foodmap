from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,LocationMessage
)

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('BoKpSTL4JjFTe9+x/CqKVQvzikeizZQ3A2Jmw1mVAhmCU5sLqi6kMbCpslBagPon7OKjG37LLrxC7Jw+IZQhCT4fe501a8DX+69JDgbDJwtznkL7UX57698MRRmR7qc5q7I4BURtw7/+5A83vyCJqQdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('844a89ee1dc510011e9869fb7dc6c4fd')

# 監聽所有來自 /callback 的 Post Request
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

@handler.default()
def default(event):
    print(event)

@handler.add(MessageEvent, message=LocationMessage)
def handle_lcationmessage(event):
    print("call handle_lcationmessage sucess")
    print(event)
    #if(event.message.location !="") :
    #    print("address:"+evevt.source.location.address)
    #    print("latitude:"+evevt.source.location.latitude)
    #    print("longitude:"+evevt.source.location.longitude)
    
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    replay_message(event,message)
    content = "{}: {}".format(event.source.user_id, event.message.text)
    #if(event.message.location !="") :
    #    print("address:"+evevt.source.location.address)
    #    print("latitude:"+evevt.source.location.latitude)
    #    print("longitude:"+evevt.source.location.longitude)
    
    try:
        profile = line_bot_api.get_profile(event.source.user_id)
        print(profile.display_name)
        print(profile.user_id)
        print(profile.picture_url)
        print(profile.status_message)
    except LineBotApiError as e:
        print(e)
    print(content)

        
def replay_message(event,text):
    line_bot_api.reply_message(
        event.reply_token,
        text)       
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
