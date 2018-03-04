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
    print("enter default")
    print(event)
    if(event.type=="postback"):
        if (event.source.user_id in serch_location) == False:
            serch_location = {}
            serch_location[event.source.user_id]=event.source.user_id
            if(event.postback.data != "other"):
                serch_location["search_kind"]=event.postback.data            
                message = TextSendMessage(text= "請輸入想要搜尋的地址 範例 #地址,台北火車站")
            else:          
                message = TextSendMessage(text= "請輸入想要搜尋的種類,地址 範例 #地址,日本料理,台北火車站")
            replay_message(event,message)
        elif((event.source.user_id in serch_location)):
            if(event.source.type == 'user'):
                push_userid = event.source.user_id
            elif(event.source.type == 'group'):
                push_userid = event.source.group_id
            if("search_kind" in serch_location):
                if("address" in serch_location):
                    address_tmp = serch_location["address"].split('#')[1];
                    url= 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+serch_location["search_kind"]+'+in+'+address_tmp+'&key='+googlekey
                    req = requests.get(url)#發送請求
                    drink_json = json.loads(req.text) 
                    columns_list=[]
                    if(len(drink_json['results']) >= 1):
                        for i in range(len(drink_json['results'])):
                            if( 'photos' in drink_json['results'][i]):
                                photo_reference_str = drink_json['results'][i]['photos'][0]['photo_reference']
                                url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=300&photoreference="+photo_reference_str+"&key="+googlekey
                            else :
                                url_photo = ""
                            address_url = 'https://www.google.com/maps/search/?api=1&query='+str(drink_json['results'][i]['geometry']['location']['lat'])+','+str(drink_json['results'][i]['geometry']['location']['lng'])+'&query_place_id='+str(drink_json['results'][i]['place_id'])
                            actions_tmp=[MessageTemplateAction(label=drink_json['results'][i]['vicinity'],text=drink_json['results'][i]['vicinity']),
                                    URITemplateAction(
                                        label='位置',
                                        uri=address_url
                                    )]
                            if(url_photo!="") and('rating' in drink_json['results'][i]) and ('name' in drink_json['results'][i]):
                                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = drink_json['results'][i]['name'],text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",actions=[MessageTemplateAction(label=drink_json['results'][i]['vicinity'],text=drink_json['results'][i]['vicinity']),
                                        URITemplateAction(
                                            label='位置',
                                            uri=address_url
                                        )]))
                            elif(url_photo!="") and ('name' in drink_json['results'][i]) :
                                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = drink_json['results'][i]['name'],text="沒有推薦資料",actions=[MessageTemplateAction(label=drink_json['results'][i]['vicinity'],text=drink_json['results'][i]['vicinity']),
                                            URITemplateAction(
                                                label='位置',
                                                uri=address_url
                                            )]))
                            if(i >=4): 
                                i = len(drink_json['results'])
                                break        
                        carousel_template_message = TemplateSendMessage(
                            alt_text='Carousel template',
                            template=CarouselTemplate(columns=columns_list)
                        )
                        #print(carousel_template_message)
                        push_message(push_userid,carousel_template_message)
                    else:
                        message = TextSendMessage(text= "抱歉該位置附近沒有"+serch_location["search_kind"]+"唷，可以試著打出更詳細地址或者搜尋其他地址")
                        push_message(push_userid,message)
                else:
                    message = TextSendMessage(text= "請輸入想要搜尋的地址 範例 #地址,台北火車站")
                    replay_message(event,message)
@handler.add(MessageEvent, message=LocationMessage)
def handle_lcationmessage(event):
    #print("call handle_lcationmessage sucess")
    #print(event)
    #print("address:"+str(event.message.address))
    #print("latitude:"+str(event.message.latitude))
    #print("longitude:"+str(event.message.longitude))
    latitude = event.message.latitude
    longitude = event.message.longitude
    isTaiwan = True
    if("台灣" in event.message.address) or ("台湾" in event.message.address):
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(latitude)+','+str(longitude)+'&radius=500&language=zh-TW&opennow&type=restaurant&key='+googlekey
        #print("address 包含 台灣")
    else:
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location='+str(latitude)+','+str(longitude)+'&radius=500&language=en&opennow&type=restaurant&key='+googlekey
        isTaiwan = False
        #print("address 沒有 台灣") 
    #print(url)        
    req = requests.get(url)#發送請求
    foodinfo = json.loads(req.text)
    #print(event)
    if(event.source.type == 'user'):
        push_userid = event.source.user_id
    elif(event.source.type == 'group'):
        push_userid = event.source.group_id
    #print(str(push_userid))    
    columns_list=[]
    url_photo_flag = False
    #print(foodinfo)
    if(len(foodinfo['results']) >= 1):
        for i in range(len(foodinfo['results'])):
            if( 'photos' in foodinfo['results'][i]):
                photo_reference_str = foodinfo['results'][i]['photos'][0]['photo_reference']
                url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=200&photoreference="+photo_reference_str+"&key="+googlekey
            else :
                url_photo = ""
            address_url = 'https://www.google.com/maps/search/?api=1&query='+str(foodinfo['results'][i]['geometry']['location']['lat'])+','+str(foodinfo['results'][i]['geometry']['location']['lng'])+'&query_place_id='+str(foodinfo['results'][i]['place_id'])
            if(url_photo != ""):
                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = foodinfo['results'][i]['name'],text="網友推薦指數:"+str(foodinfo['results'][i]['rating'])+"/5",actions=[MessageTemplateAction(label=foodinfo['results'][i]['vicinity'],text=foodinfo['results'][i]['vicinity']),
                        URITemplateAction(
                            label='位置',
                            uri=address_url
                        )]))            
            if(i >=8): 
                i = len(foodinfo['results'])
                break
        #print(str(len(columns_list)))
        carousel_template_message = TemplateSendMessage(
                alt_text='Carousel template',
                template=CarouselTemplate(columns=columns_list)
                )
        """    
        if(len(columns_list) >=9) :        
            carousel_template_message = TemplateSendMessage(
                alt_text='Carousel template',
                template=CarouselTemplate(columns=[columns_list[0],
                columns_list[1],
                columns_list[2],
                columns_list[3]])
            )
        elif( len(columns_list) >=5 and len(columns_list) < 9):
            carousel_template_message = TemplateSendMessage(
                alt_text='Carousel template',
                template=CarouselTemplate(columns=[columns_list[0],
                columns_list[1],
                columns_list[2],
                columns_list[3]])
            )
        elif( len(columns_list) >=3 and len(columns_list) < 5):
            carousel_template_message = TemplateSendMessage(
                alt_text='Carousel template',
                template=CarouselTemplate(columns=[columns_list[0],
                columns_list[1],
                columns_list[2]])
            )
        elif( len(columns_list) >=1 and len(columns_list) < 3):
            carousel_template_message = TemplateSendMessage(
                alt_text='Carousel template',
                template=CarouselTemplate(columns=[columns_list[0]])
            )
        else:
            carousel_template_message = TextSendMessage(text= "抱歉該位置附近沒有餐廳唷，可以試著移動地址在試一次")
        """    
        #print(columns_list)
        #print(carousel_template_message)
        replay_message(event,carousel_template_message)
        #push_message(push_userid,carousel_template_message)
    else:
        message = TextSendMessage(text= "抱歉該位置附近沒有餐廳唷，可以試著移動地址在試一次")
        #push_message(push_userid,message)
        replay_message(event,message)
    #print(req.text)    
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
        url= 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+search_kind_tmp+'+in+'+address_tmp+"&radius=100&language=zh-TW"+'&key='+googlekey
        #print(event.message.text.split(','))
        print(url)
        req = requests.get(url)#發送請求
        drink_json = json.loads(req.text) 
        columns_list=[]
        if(len(drink_json['results']) >= 1):
            for i in range(len(drink_json['results'])):
                if ("formatted_address" in drink_json['results'][i]) and ("name" in drink_json['results'][i]):
                    if( 'photos' in drink_json['results'][i]):
                        photo_reference_str = drink_json['results'][i]['photos'][0]['photo_reference']
                        url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=200&photoreference="+photo_reference_str+"&key="+googlekey
                    else :
                        url_photo = ""  
                    address_url = "https://www.google.com/maps/search/?api=1&query="+str(drink_json['results'][i]['geometry']['location']['lat'])+","+str(drink_json['results'][i]['geometry']['location']['lng'])+"&query_place_id="+str(drink_json['results'][i]['place_id'])
                    #print("title:"+drink_json['results'][i]['name'])
                    #print("title length :"+str(len(drink_json['results'][i]['name'])))
                    #print("thumbnail_image_url :"+str(url_photo_flag))
                    #print("label :"+drink_json['results'][i]['formatted_address'])
                    #print("label length :"+str(len(drink_json['results'][i]['formatted_address'])))
                    #print("label type:"+str(type(drink_json['results'][i]['formatted_address'])))
                    #print("address_url :"+address_url)
                    tmp_string = str(drink_json['results'][i]["formatted_address"]).split("台灣",1)
                    print(tmp_string)
                    label_string="地址:"
                    if(len(tmp_string) >=2):
                        label_string = label_string+tmp_string[1]
                    else:
                        label_string = label_string+FullToHalf(drink_json['results'][i]["formatted_address"])
                    print(FullToHalf(drink_json['results'][i]["formatted_address"]))
                    columns_list.append(
                    CarouselColumn(
                        thumbnail_image_url=url_photo,
                        title=drink_json['results'][i]['name'],
                        text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",
                        actions=[
                            MessageTemplateAction(
                                label=label_string,
                                text=label_string
                            ),
                            URITemplateAction(label='位置',uri=address_url)]
                            )
                    )
                    carousel_template_message = TemplateSendMessage(
                        alt_text='Drink carousel',
                        template=CarouselTemplate(
                            columns=[
                                CarouselColumn(
                                    thumbnail_image_url=url_photo,
                                    title=drink_json['results'][i]['name'],
                                    text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",
                                    actions=[
                                        MessageTemplateAction(
                                            label=label_string,
                                            text="test"
                                        ),
                                        URITemplateAction(
                                            label='位置',
                                            uri=address_url
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                    #push_message(event.source.user_id,carousel_template_message)
                if(i >=6): 
                    i = len(drink_json['results'])
                    break
            carousel_template_message = TemplateSendMessage(
                alt_text='Drink carousel',
                template=CarouselTemplate(columns=columns_list))
            push_message(push_userid,carousel_template_message)
        else:
            message = TextSendMessage(text= "抱歉該位置附近沒有"+search_kind_tmp+"唷，可以試著打出更詳細地址或者搜尋其他地址")
            push_message(push_userid,message)
    elif(event.source.user_id in serch_location) and ( "#地址" in event.message.text): 
            if(event.source.type == 'user'):
                push_userid = event.source.user_id
            elif(event.source.type == 'group'):
                push_userid = event.source.group_id
            url_photo_flag = True    
            if("search_kind" in serch_location):
                if ("address" in serch_location) == False :
                    address_tmp = event.message.text.split(',')[1];
                    url= 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+serch_location["search_kind"]+'+in+'+address_tmp+'&key='+googlekey
                    print(event.message.text.split(','))
                    print(url)
                    req = requests.get(url)#發送請求
                    drink_json = json.loads(req.text) 
                    columns_list=[]
                    if(len(drink_json['results']) >= 1):
                        for i in range(len(drink_json['results'])):
                            if ("formatted_address" in drink_json['results'][i]) and ("name" in drink_json['results'][i]):
                                if( 'photos' in drink_json['results'][i]):
                                    photo_reference_str = drink_json['results'][i]['photos'][0]['photo_reference']
                                    url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=300&photoreference="+photo_reference_str+"&key="+googlekey
                                else :
                                    url_photo = ""
                                req_photo = requests.get(url_photo)
                                if(req_photo.status_code == 200):
                                    url_photo_flag =True
                                else:
                                    url_photo_flag = False
                                address_url = 'https://www.google.com/maps/search/?api=1&query='+str(drink_json['results'][i]['geometry']['location']['lat'])+','+str(drink_json['results'][i]['geometry']['location']['lng'])+'&query_place_id='+str(drink_json['results'][i]['place_id'])
                                actions_tmp=[MessageTemplateAction(label=drink_json['results'][i]['formatted_address'],text=drink_json['results'][i]['formatted_address']),
                                        URITemplateAction(
                                            label='位置',
                                            uri=address_url
                                        )]
                                if(url_photo_flag) and('formatted_address' in drink_json['results'][i]) and ('name' in drink_json['results'][i]):
                                    columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = drink_json['results'][i]['name'],text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",actions=[MessageTemplateAction(label=drink_json['results'][i]['formatted_address'],text=drink_json['results'][i]['formatted_address']),
                                            URITemplateAction(
                                                label='位置',
                                                uri=address_url
                                            )]))
                                elif(url_photo_flag) and ('name' in drink_json['results'][i]) :
                                    columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = drink_json['results'][i]['name'],text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",actions=[MessageTemplateAction(label="無法顯示地址",text="無法顯示地址"),
                                                URITemplateAction(
                                                    label='位置',
                                                    uri=address_url
                                                )]))
                            if(i >=6): 
                                i = len(drink_json['results'])
                                break
                        if(len(columns_list) >=5):            
                            carousel_template_message = TemplateSendMessage(
                                alt_text='Carousel template',
                                template=CarouselTemplate(columns=[columns_list[0],
                                columns_list[1],
                                columns_list[2],
                                columns_list[3],
                                columns_list[4]])
                            )
                        elif(len(columns_list) == 4):
                            carousel_template_message = TemplateSendMessage(
                                alt_text='Carousel template',
                                template=CarouselTemplate(columns=[columns_list[0],
                                columns_list[1],
                                columns_list[2],
                                columns_list[3]])
                            )
                        elif(len(columns_list) == 3):
                            carousel_template_message = TemplateSendMessage(
                                alt_text='Carousel template',
                                template=CarouselTemplate(columns=[columns_list[0],
                                columns_list[1],
                                columns_list[2]])
                            )
                        elif(len(columns_list) == 2):
                            carousel_template_message = TemplateSendMessage(
                                alt_text='Carousel template',
                                template=CarouselTemplate(columns=[columns_list[0],
                                columns_list[1]])
                            )
                        elif(len(columns_list) == 1):
                            carousel_template_message = TemplateSendMessage(
                                alt_text='Carousel template',
                                template=CarouselTemplate(columns=[columns_list[0]])
                            )
                        else:
                            carousel_template_message = TextSendMessage(text= "抱歉該位置附近沒有"+serch_location["search_kind"]+"唷，可以試著打出更詳細地址或者搜尋其他地址")
                        #print(carousel_template_message)
                        replay_message(event,carousel_template_message)
                        #push_message(push_userid,carousel_template_message)
                    else:
                        message = TextSendMessage(text= "抱歉該位置附近沒有"+serch_location["search_kind"]+"唷，可以試著打出更詳細地址或者搜尋其他地址")
                        replay_message(event,message)
                        #push_message(push_userid,message)
            else:
                search_kind_tmp = address_tmp = event.message.text.split(',')[1];
                address_tmp = event.message.text.split(',')[2];
                url= 'https://maps.googleapis.com/maps/api/place/textsearch/json?query='+search_kind_tmp+'+in+'+address_tmp+'&key='+googlekey
                print(event.message.text.split(','))
                print(url)
                req = requests.get(url)#發送請求
                drink_json = json.loads(req.text) 
                columns_list=[]
                if(len(drink_json['results']) >= 1):
                    for i in range(len(drink_json['results'])):
                        if ("formatted_address" in drink_json['results'][i]) and ("name" in drink_json['results'][i]):
                            if( 'photos' in drink_json['results'][i]):
                                photo_reference_str = drink_json['results'][i]['photos'][0]['photo_reference']
                                url_photo = "https://maps.googleapis.com/maps/api/place/photo?maxwidth=300&photoreference="+photo_reference_str+"&key="+googlekey
                            else :
                                url_photo = ""
                            address_url = 'https://www.google.com/maps/search/?api=1&query='+str(drink_json['results'][i]['geometry']['location']['lat'])+','+str(drink_json['results'][i]['geometry']['location']['lng'])+'&query_place_id='+str(drink_json['results'][i]['place_id'])
                            actions_tmp=[MessageTemplateAction(label=drink_json['results'][i]['formatted_address'],text=drink_json['results'][i]['formatted_address']),
                                    URITemplateAction(
                                        label='位置',
                                        uri=address_url
                                    )]
                            if(url_photo!="") and('formatted_address' in drink_json['results'][i]) and ('name' in drink_json['results'][i]):
                                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = drink_json['results'][i]['name'],text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",actions=[MessageTemplateAction(label=drink_json['results'][i]['formatted_address'],text=drink_json['results'][i]['formatted_address']),
                                        URITemplateAction(
                                            label='位置',
                                            uri=address_url
                                        )]))
                            elif(url_photo!="") and ('name' in drink_json['results'][i]) :
                                columns_list.append(CarouselColumn(thumbnail_image_url = url_photo,title = drink_json['results'][i]['name'],text="網友推薦指數:"+str(drink_json['results'][i]['rating'])+"/5",actions=[MessageTemplateAction(label="無法顯示地址",text="無法顯示地址"),
                                            URITemplateAction(
                                                label='位置',
                                                uri=address_url
                                            )]))
                        if(i >=6): 
                            i = len(drink_json['results'])
                            break
                    if(len(columns_list) >=5):            
                        carousel_template_message = TemplateSendMessage(
                            alt_text='Carousel template',
                            template=CarouselTemplate(columns=[columns_list[0],
                            columns_list[1],
                            columns_list[2],
                            columns_list[3],
                            columns_list[4]])
                        )
                    elif(len(columns_list) == 4):
                        carousel_template_message = TemplateSendMessage(
                            alt_text='Carousel template',
                            template=CarouselTemplate(columns=[columns_list[0],
                            columns_list[1],
                            columns_list[2],
                            columns_list[3]])
                        )
                    elif(len(columns_list) == 3):
                        carousel_template_message = TemplateSendMessage(
                            alt_text='Carousel template',
                            template=CarouselTemplate(columns=[columns_list[0],
                            columns_list[1],
                            columns_list[2]])
                        )
                    elif(len(columns_list) == 2):
                        carousel_template_message = TemplateSendMessage(
                            alt_text='Carousel template',
                            template=CarouselTemplate(columns=[columns_list[0],
                            columns_list[1]])
                        )
                    elif(len(columns_list) == 1):
                        carousel_template_message = TemplateSendMessage(
                            alt_text='Carousel template',
                            template=CarouselTemplate(columns=[columns_list[0]])
                        )
                    else:
                        carousel_template_message = TextSendMessage(text= "抱歉該位置附近沒有"+search_kind_tmp+"唷，可以試著打出更詳細地址或者搜尋其他地址")
                    #print(carousel_template_message)
                    push_message(push_userid,carousel_template_message)
                    serch_location = []
                else:
                    message = TextSendMessage(text= "抱歉該位置附近沒有"+search_kind_tmp+"唷，可以試著打出更詳細地址或者搜尋其他地址")
                    push_message(push_userid,message)
        #push_message(push_userid,buttons_template_message)
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

def FullToHalf(s): 
    n = []
    print(s)    
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

"""
def str_full_to_half(ustring):

    Adapt from http://www.pythonclub.org/python-scripts/quanjiao-banjiao

    out_str = []
    for char in ustring:
        inside_code = ord(char)
        if(inside_code == 0x3000):
            inside_code = 0x0020  # space
        elif(0xFF01>=inside_code and inside_code<=0xFF5E):
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e:
            out_str.append(char)
        out_str.append(chr(inside_code))
    return ''.join(out_str)
"""  
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
