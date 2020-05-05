
# coding: utf-8

# In[ ]:


'''

整體功能描述

'''

# In[ ]:

'''

Application 主架構

'''

from confluent_kafka import Producer
import redis
import sys, datetime
import os, cv2
import util
import numpy as np
import requests
import urllib
from io import BytesIO

path1 = os.getcwd()
print(path1)


# 引用Web Server套件
from flask import Flask, request, abort

# 從linebot 套件包裡引用 LineBotApi 與 WebhookHandler 類別
from linebot import (
    LineBotApi, WebhookHandler
)

# 引用無效簽章錯誤
from linebot.exceptions import (
    InvalidSignatureError
)

# 載入json處理套件
import json

# 載入基礎設定檔
secretFileContentJson=json.load(open("./line_secret_key",'r',encoding='utf8'))
# server_url=secretFileContentJson.get("server_url")

# 設定Server啟用細節
app = Flask(__name__,static_url_path = "/素材" , static_folder = "./素材/")

# print("token:", secretFileContentJson.get("channel_access_token"))
# print("key:", secretFileContentJson.get("secret_key"))
# print("server:", secretFileContentJson.get("server_url"))

# 生成實體物件
line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))
handler = WebhookHandler(secretFileContentJson.get("secret_key"))
ques_url = secretFileContentJson.get("ques_url")

# 啟動server對外接口，使Line能丟消息進來
@app.route("/", methods=['POST'])
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


# In[ ]:


'''

消息判斷器

讀取指定的json檔案後，把json解析成不同格式的SendMessage

讀取檔案，
把內容轉換成json
將json轉換成消息
放回array中，並把array傳出。

'''

# 引用會用到的套件
from linebot.models import (
    ImagemapSendMessage,TextSendMessage,ImageSendMessage,LocationSendMessage,FlexSendMessage,VideoSendMessage,StickerSendMessage
)


from linebot.models.template import (
    ButtonsTemplate,CarouselTemplate,ConfirmTemplate,ImageCarouselTemplate
    
)

from linebot.models.template import *

def detect_json_array_to_new_message_array(fileName):
    
    #開啟檔案，轉成json
    with open(fileName,encoding = 'utf-8') as f:
        jsonArray = json.load(f)
    
    # 解析json
    returnArray = []
    for jsonObject in jsonArray:

        # 讀取其用來判斷的元件
        message_type = jsonObject.get('type')
        
        # 轉換
        if message_type == 'text':
            returnArray.append(TextSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'imagemap':            returnArray.append(ImagemapSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'template':            returnArray.append(TemplateSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'image':
            returnArray.append(ImageSendMessage.new_from_json_dict(jsonObject))
#         elif message_type == 'sticker':            returnArray.append(StickerSendMessage.new_from_json_dict(jsonObject))  
#         elif message_type == 'audio':
#             returnArray.append(AudioSendMessage.new_from_json_dict(jsonObject)) 
        elif message_type == 'location':            returnArray.append(LocationSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'flex':
            returnArray.append(FlexSendMessage.new_from_json_dict(jsonObject)) 
#         elif message_type == 'video':
#             returnArray.append(FlexSendMessage.new_from_json_dict(jsonObject))    
    # 回傳
    return returnArray

# ---------------------------------------------------

def getQuestionnaireReply(reToken, fileName):
    # 開啟檔案，轉成json
    with open(fileName, "r", encoding="utf-8") as fi:
        #print(fi.read())
        #print(type(fi.read()))
        jsonStr = fi.read()
        jsonStr = jsonStr.replace("{url}", "{0}?linebottoken={1}".format(ques_url, reToken))
        ##jsonStr = fi.read().replace("{url}", "{0}?linebottoken={1}".format(ques_url, reToken))
        print("jsonStr:", jsonStr)
        jsonArray = json.loads(jsonStr)

    # 解析json
    returnArray = []
    for jsonObject in jsonArray:
        returnArray.append(TextSendMessage.new_from_json_dict(jsonObject))

    return returnArray

# ---------------------------------------------------

# In[ ]:
'''

handler處理關注消息

用戶關注時，讀取 素材 -> 關注 -> reply.json

將其轉換成可寄發的消息，傳回給Line

'''

# 引用套件
from linebot.models import (
    FollowEvent
)

# 載入Follow事情
from linebot.models.events import FollowEvent

# 載入requests事件
import requests


# 關注事件處理
@handler.add(FollowEvent)

def process_follow_event(event):   
    
    # 讀取並轉換
    result_message_array =[]
    replyJsonPath = "./素材/關注歡迎詞/reply.json"
    result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

    # 消息發送
    line_bot_api.reply_message(
        event.reply_token,
        result_message_array
    )

    
# def reply_text_and_get_user_profile(event):
#     # 取出消息內的user資料
#     user_profile = line_bot_api.get_profile(event.source.user_id)
    
#     # 將用戶檔案存起來
#     with open("./users.txt", "a") as myfile:
#         myfile.write(json.dumps(vars(user_profile),sort_keys=True))
#         myfile.write("\r")
#         myfile.close()     
    
#     # 回覆消息
#     line_bot_api.reply_message(
#         event.reply_token,
#         result_message_list
#     )


# ================================================================

# ===============================================================


# In[ ]:

'''
handler處理文字消息

收到用戶回應的文字消息，

'''

# 引用套件
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,  PostbackEvent
)

    
# 文字消息處理
# @handler.add(MessageEvent,message=TextMessage)
@handler.add(MessageEvent)

def process_text_message(event):
    #print("message:", event.message)
    #print("type:", event.message.type)
    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)
    #print("user_profile:", user_profile)
    userName = json.loads(json.dumps(vars(user_profile),sort_keys=True))["display_name"]
    
    # 讀取圖片檔做影像辨視
    if event.message.type == "image":
        message_content = line_bot_api.get_message_content(event.message.id)
        with open("./{0}.jpg".format(event.reply_token), 'wb') as fd:
            for chunk in message_content.iter_content():
                fd.write(chunk)

        img1 = cv2.imread("./{0}.jpg".format(event.reply_token), 1)
        retval, buffer = cv2.imencode('.jpg', img1)
        img1_bytes = np.array(buffer).tostring()

        #print("token:", event.reply_token)
        util.setRedisImg(event.reply_token, img1_bytes)

        file = util.getRedisImg(event.reply_token)
        #print("file:", file)    
    
    else:
        # 讀取本地檔案，並轉譯成消息
        result_message_array =[]
        if event.message.text in os.listdir(r'./素材'):
            
            replyJsonPath = "素材/"+event.message.text+"/reply.json"
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)

            # 發送
            line_bot_api.reply_message(
                event.reply_token,
                result_message_array
            )
            
#         elif event.message.text=='ok':  #觸發 quick_reply
            
#             # 發送
#             line_bot_api.reply_message(
#             event.reply_token,
#             template_message_dict.get(event.message.text)
#             )
          
        elif event.message.text in util.getSiteList():
#             prod = util.getProducer()
#             # 步驟3. 指定想要發佈訊息的topic名稱
#             topicName = 'test1'
#             util.sendKafkaMsg(topicName, event.message.text, event.reply_token)

#             re = util.getRedis()
#             tnow = datetime.datetime.now()

#             value = re.get(event.reply_token)
            
            
#             try:
#                 while value == None:
#                     value = re.get(event.reply_token)

#                     diff = (datetime.datetime.now() - tnow).total_seconds()
#                     print("seconds:", diff)
#                     assert diff < 30, "over time error"
#             except AssertionError as error:
#                 print(error)
#                 return

#             print(value)
            
            
            value = ["金瓜石, 正濱漁港, 阿根納遺址, 龍磐步道", "小人國主題樂園,慈湖陵寢,石門水壩,小烏來天空步道", "龜山島,太平山國家森林遊樂區,羅東夜市,冬山河親水公園"]

            siteList = value[random.randint(0,3)].split(",")
            print("siteList:", siteList)
            replyMsg = util.getTemplateJson();
            for i, site in enumerate(siteList):
                replyMsg = replyMsg.replace("site{}".format(i + 1), site)

            print("replyMsg:", replyMsg)
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage.new_from_json_dict(json.loads(replyMsg))
            )
            
            elkDoc = {}
            elkDoc["UserName"] = userName
            elkDoc["Place"] = event.message.text
            elkDoc["Recommedation"] = siteList
            elkDoc["DateTime"] = datetime.datetime.now()
            util.insertELK("rsite", elkDoc)
            
            
        else:
            return

        
#---------------------------
# '''

# 若收到圖片消息時，

# 先回覆用戶文字消息，並從Line上將照片拿回。

# '''

# @handler.add(MessageEvent, message=ImageMessage) #ImageMessage:傳圖片給line機器人，他會回傳給你東西
# def handle_message(event):   #reply_message 被動收到訊息
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text='Image has Upload'+ ' ' + event.message.id))
#     message_content = line_bot_api.get_message_content(event.message.id)
#     with open('./images/'+event.message.id+'.jpg', 'wb') as fd:
#         for chunk in message_content.iter_content():
#             fd.write(chunk)

# ----------------------------
# In[ ]:


'''

handler處理Postback Event

載入功能選單與啟動特殊功能

解析postback的data，並按照data欄位判斷處理

現有三個欄位
menu, folder, tag

若folder欄位有值，則
    讀取其reply.json，轉譯成消息，並發送

若menu欄位有值，則
    讀取其rich_menu_id，並取得用戶id，將用戶與選單綁定
    讀取其reply.json，轉譯成消息，並發送

'''
from linebot.models import (
    PostbackEvent
)

from urllib.parse import parse_qs 

# 引入相關套件
from linebot.models import (
    MessageAction, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    QuickReply, QuickReplyButton
)

@handler.add(PostbackEvent)
def process_postback_event(event):
    result_message_array = []
    replyJsonPath = r"./素材/{0}/reply.json".format(event.postback.data)
    print("replyJsonPath:", replyJsonPath)
    print("answer:", event.postback.data.find(":::Q"))
    user_profile = line_bot_api.get_profile(event.source.user_id)
    print("user_profile:", type(json.dumps(vars(user_profile),sort_keys=True)))
    userName = json.loads(json.dumps(vars(user_profile),sort_keys=True))["display_name"]
    
    if event.postback.data == "回答幾個問題讓我們更了解您的旅遊喜好吧":
        replyJsonPath = r"./素材/Q1/reply.json"
        result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
        line_bot_api.reply_message(
            event.reply_token,
            result_message_array
        )
    elif event.postback.data.find(":::Q") >= 1:
        idx = event.postback.data[5:6]
        print("idx:", idx)
        if idx == "5":
            print("return result")
            timestamp = datetime.datetime.now().strftime("%Y%m%d")
            answer = event.postback.data[9:]
            key = "{0}-{1}".format(userName, timestamp)
            util.redisLPush(key, answer)

            allAnswer = util.redisLRange(key, 0, -1)
            print("allAnswer:", allAnswer)
            doc = {}
            score = 0
            for an in allAnswer:
                doc[an] = score + 1
            util.sendKafkaMsg("questionaire", doc, event.reply_token)\
            
            elkDoc = {}
            elkDoc["key"] = key
            elkDoc["UserName"] = userName
            elkDoc["DateTime"] = datetime.datetime.now()
            for i, an in enumerate(allAnswer):
                elkDoc["item{0}".format(i+1)] = an

            util.insertELK("questionaire", elkDoc)
            #把redis資料清空
            util.redisLPopAll(key)            
            
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d")
            answer = event.postback.data[9:]
            util.redisLPush("{0}-{1}".format(userName, timestamp), answer)

            replyJsonPath = r"./素材/Q{0}/reply.json".format(int(idx) + 1)
            result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
            line_bot_api.reply_message(
                event.reply_token,
                result_message_array
            )

    elif event.postback.data.find("Photo") > 1:
        ## 點擊後，切換至照片相簿選擇
        cameraRollQRB = QuickReplyButton(
            action=CameraRollAction(label="上傳照片")
        )

        quickReplyList = QuickReply(
            items=[cameraRollQRB]
        )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='上傳照片解鎖旅遊成就', quick_reply=quickReplyList)
        )
    elif event.postback.data.find("Camera") > 1:
        ## CameraAction
        cameraQuickReplyButton = QuickReplyButton(
            action=CameraAction(label="拍照解鎖")
        )
        quickReplyList = QuickReply(
            items=[cameraQuickReplyButton]
        )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='拍照解鎖旅遊成就', quick_reply=quickReplyList)
        )
            
            
    else:
        result_message_array = detect_json_array_to_new_message_array(replyJsonPath)
        line_bot_api.reply_message(
            event.reply_token,
            result_message_array
        )


# In[ ]:


'''

Application 運行（開發版）

'''
if __name__ == "__main__":
    app.run(host='0.0.0.0')


# In[ ]:


'''

Application 運行（heroku版）

'''

# import os
# if __name__ == "__main__":
#     app.run(host='0.0.0.0',port=os.environ['PORT'])

