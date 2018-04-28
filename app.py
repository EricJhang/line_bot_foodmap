from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,LocationMessage,LocationSendMessage,TemplateSendMessage,CarouselTemplate,CarouselColumn,MessageTemplateAction,PostbackTemplateAction,URITemplateAction,ButtonsTemplate,PostbackEvent
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
tmp_count = 0
serch_location = {}
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
    global tmp_count
    global serch_location
    print(event)
    push_userid =""
    if(event.source.type == 'user'):
        push_userid = event.source.user_id
    elif(event.source.type == 'group'):
        push_userid = event.source.group_id
    if(event.type =="postback"):
        event.postback.data
        url_detal = "https://maps.googleapis.com/maps/api/place/details/json?placeid="+event.postback.data+"&language=zh-TW&key="+googlekey
        print(url_detal)
        req_detal = requests.get(url_detal)#發送請求
        detal_json = json.loads(req_detal.text)
        reviews_text=""
        if("reviews" in detal_json['result']):
            if(len(detal_json['result']["reviews"])>=1):
                for i in range(len(detal_json['result']["reviews"])):
                    reviews_text =reviews_text+"評分:"+str(detal_json['result']["reviews"][i]["rating"])+"/5\n"+ "評論:"+detal_json['result']["reviews"][i]["text"]+"\n\n"
            else:
                reviews_text ="沒有評論"
        else:
            reviews_text ="沒有評論"
        message = TextSendMessage(text= reviews_text)
        push_message(push_userid,message)
    
@handler.add(MessageEvent, message=LocationMessage)
def handle_lcationmessage(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    if("台灣" in event.message.address) or ("台湾" in event.message.address):
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(latitude)+','+str(longitude)+'&radius=500&language=zh-TW&opennow&type=restaurant&key='+googlekey
    else:
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(latitude)+','+str(longitude)+'&radius=500&language=en&opennow&type=restaurant&key='+googlekey    
    req = requests.get(url)#發送請求
    foodinfo = json.loads(req.text)
    if(event.source.type == 'user'):
        push_userid = event.source.user_id
    elif(event.source.type == 'group'):
        push_userid = event.source.group_id  
    columns_list=[]
    url_photo_flag = False
    if(len(foodinfo['results']) >= 1):
        for i in range(len(foodinfo['results'])):
            if( 'photos' in foodinfo['results'][i]):
                photo_reference_str = foodinfo['results'][i]['photos'][0]['photo_reference']
                url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=200&photoreference="+photo_reference_str+"&key="+googlekey
            else :
                url_photo = ""
            address_url = 'https://www.google.com/maps/search/?api=1&query='+str(foodinfo['results'][i]['geometry']['location']['lat'])+','+str(foodinfo['results'][i]['geometry']['location']['lng'])+'&query_place_id='+str(foodinfo['results'][i]['place_id'])
            if(url_photo != "") and ('rating' in foodinfo['results'][i]):
                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = foodinfo['results'][i]['name'],text="網友推薦指數:"+str(foodinfo['results'][i]['rating'])+"/5",actions=[
                        MessageTemplateAction(label="地址",text=foodinfo['results'][i]['vicinity']),
                        URITemplateAction(
                            label='位置',
                            uri=address_url
                        ),
                        PostbackTemplateAction(
                                        label='評論',
                                        data=foodinfo['results'][i]['place_id']
                                    )
                        ]))            
            if(i >=8): 
                i = len(foodinfo['results'])
                break
        carousel_template_message = TemplateSendMessage(
                alt_text='美食搜尋結果',
                template=CarouselTemplate(columns=columns_list)
                )
        push_message(push_userid,carousel_template_message)
    else:
        message = TextSendMessage(text= "抱歉該位置附近沒有餐廳唷，可以試著移動地址在試一次")
        #push_message(push_userid,message)
        replay_message(event,message)
  
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global serch_location
    message = TextSendMessage(text=event.message.text)
    print(event)
    print(event.message.text)
    print(message)
    global tmp_count
    url_photo_flag = True
    if(event.source.type == 'user'):
        push_userid = event.source.user_id
    elif(event.source.type == 'group'):
        push_userid = event.source.group_id   
    if(event.message.text == "#搜尋") or (event.message.text == "#找餐廳"):      
        message = TextSendMessage(text= "請輸入格式 #搜尋,搜尋種類,搜尋地址\n範例說明: #搜尋,飲料,台北車站")
        replay_message(event,message)
    elif( "#搜尋" in event.message.text) and (len(event.message.text.split(',')) >=2 ) :
        search_kind_tmp = address_tmp = event.message.text.split(',')[1];
        address_tmp = event.message.text.split(',')[2];
        url= 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+search_kind_tmp+'+'+address_tmp+"&rankby=prominence&language=zh-TW"+'&key='+googlekey
        print(url)
        req = requests.get(url)#發送請求
        drink_json = json.loads(req.text) 
        columns_list=[]
        if(len(drink_json['results']) >= 1):
            for i in range(len(drink_json['results'])):
                if ("formatted_address" in drink_json['results'][i]) and ("name" in drink_json['results'][i]) and ('rating' in drink_json['results'][i]):
                    if( 'photos' in drink_json['results'][i]):
                        photo_reference_str = drink_json['results'][i]['photos'][0]['photo_reference']
                        url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=200&photoreference="+photo_reference_str+"&key="+googlekey
                    else :
                        url_photo = ""  
                    address_url = "https://www.google.com/maps/search/?api=1&query="+str(drink_json['results'][i]['geometry']['location']['lat'])+","+str(drink_json['results'][i]['geometry']['location']['lng'])+"&query_place_id="+str(drink_json['results'][i]['place_id'])
                    label_string="地址:"
                    label_string = label_string+FullToHalf(drink_json['results'][i]["formatted_address"])
                    if(url_photo != "" ):                        
                        columns_list.append(
                            CarouselColumn(
                                thumbnail_image_url=url_photo,
                                title=drink_json['results'][i]['name'],
                                text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",
                                actions=[
                                    MessageTemplateAction(
                                        label="地址",
                                        text=label_string
                                    ),
                                    URITemplateAction(label='位置',uri=address_url),
                                    PostbackTemplateAction(
                                        label='評論',
                                        data=drink_json['results'][i]['place_id']
                                    )
                                    ]
                            )                                
                        )
                if(i >=9): 
                    i = len(drink_json['results'])
                    break
            if(len(columns_list)>=1):        
                carousel_template_message = TemplateSendMessage(
                    alt_text='美食搜尋結果',
                    template=CarouselTemplate(columns=columns_list))
                push_message(push_userid,carousel_template_message)
            else:
                message = TextSendMessage(text= "抱歉該位置附近沒有"+search_kind_tmp+"唷，可以試著打出更詳細地址或者搜尋其他地址")
                push_message(push_userid,message)               
        else:
            message = TextSendMessage(text= "抱歉該位置附近沒有"+search_kind_tmp+"唷，可以試著打出更詳細地址或者搜尋其他地址")
            push_message(push_userid,message)

#全形轉半形
def FullToHalf(s): 
    n = [] 
    for char in s: 
        num = ord(char) 
        if num == 0x3000: 
            num = 32
            n.append(chr(num))    
        elif (num >= 65281 and num <= 65374): 
            num -= 65248
            n.append(chr(num))
        else:
            n.append(char)
    return ''.join(n) 

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
