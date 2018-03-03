from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,LocationMessage,LocationSendMessage,TemplateSendMessage,CarouselTemplate,CarouselColumn,MessageTemplateAction,PostbackTemplateAction,URITemplateAction
)
import requests
import json
import os
app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(os.environ["linetoken"])
# Channel Secret
handler = WebhookHandler(os.environ["linechannel"])

googlekey = os.environ["googlePreminkey"]

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
    print("address:"+str(event.message.address))
    print("latitude:"+str(event.message.latitude))
    print("longitude:"+str(event.message.longitude))
    latitude = event.message.latitude
    longitude = event.message.longitude
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(latitude)+','+str(longitude)+'&radius=500&language=zh-TW&opennow&type=restaurant&key='+googlekey
    req = requests.get(url)#發送請求
    foodinfo = json.loads(req.text)
    print(event)
    if(event.source.type == 'user'):
        push_userid = event.source.user_id
    elif(event.source.type == 'group'):
        push_userid = event.source.group_id
    print(str(push_userid))    
    columns_list=[]
    if(len(foodinfo['results']) >= 1):
        for i in range(len(foodinfo['results'])):
            if( 'photos' in foodinfo['results'][i]):
                photo_reference_str = foodinfo['results'][i]['photos'][0]['photo_reference']
                url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=300&photoreference="+photo_reference_str+"&key="+googlekey
            else :
                photo_reference_str = ""
            req_photo = requests.get(url_photo)
            address_url = 'https://www.google.com/maps/search/?api=1&query='+str(foodinfo['results'][i]['geometry']['location']['lat'])+','+str(foodinfo['results'][i]['geometry']['location']['lng'])+'&query_place_id='+str(foodinfo['results'][i]['place_id'])
            actions_tmp=[MessageTemplateAction(label=foodinfo['results'][i]['vicinity'],text=foodinfo['results'][i]['vicinity']),
                    URITemplateAction(
                        label='位置',
                        uri=address_url
                    )]
            if(photo_reference_str!="") and('vicinity' in foodinfo['results'][i]):        
                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = foodinfo['results'][i]['name'],text="網友推薦指數:"+str(foodinfo['results'][i]['rating']),actions=[MessageTemplateAction(label=foodinfo['results'][i]['vicinity'],text=foodinfo['results'][i]['vicinity']),
                        URITemplateAction(
                            label='位置',
                            uri=address_url
                        )]))
            if(i >=10): 
                i = len(foodinfo['results'])
                break            
        carousel_template_message = TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(columns=columns_list)
        )
        print(columns_list)
        print(carousel_template_message)
        push_message(push_userid,carousel_template_message)
    else:
        message = TextSendMessage(text= "抱歉該位置附近沒有餐廳唷")
        push_message(push_userid,message)
    #print(req.text)    
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = TextSendMessage(text=event.message.text)
    print(message)
    #if(message == "#美食"):
    #    None
    #replay_message(event,message)
    #content = "{}: {}".format(event.source.user_id, event.message.text)

    
    #try:
    #    profile = line_bot_api.get_profile(event.source.user_id)
    #    print(profile.display_name)
    #    print(profile.user_id)
    #    print(profile.picture_url)
    #    print(profile.status_message)
    #except LineBotApiError as e:
    #    print(e)
    #print(content)

        
def replay_message(event,text):
    line_bot_api.reply_message(
        event.reply_token,
        text)       
def push_message(userid,text):
    line_bot_api.push_message(userid,text)
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
