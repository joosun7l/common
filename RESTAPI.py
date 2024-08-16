import cv2
import numpy as np
import time
import configparser
import threading
import datetime
import json
import Message_IF
import Output_interface
import os
import Log
import pydicom_custom
import numpy as np
from flask import Flask, request, make_response
from flask_restx import Api, Resource
from werkzeug.utils import secure_filename

templateType=""

app = Flask(__name__)
api = Api(app)

#region read ini
serverInfo= configparser.ConfigParser()
serverInfo.read('Server_info.ini')
#endregion

tempList=list()

def remove_tempFile():
    while True:
        if len(tempList)>0:
            target=tempList.pop()
            os.remove(target)
        time.sleep(0.1)

#region single file upload(image)
@api.route('/visionai/asyncStillImage')
class upload_asyncfile_image(Resource):
    def post(self):
        try:
            Log.make_log(f"threads count : {threading.active_count()}")
            global templateType
            extraInfo = {}
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            if request.method == 'POST':
                receiveTime = datetime.datetime.utcnow()

                transactionId = str(int(time.time()*1000000))[-11:]
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InferenceCall","START","")
                method= "REST"
                imageMimeType = ["image/png","image/jpeg","image/bmp","image/webp"]
                Log.return_log_for_REST(request)
                try:
                    receiveFile = request.files['file']
                    Log.make_log(f"File content_type = {receiveFile.content_type}")
                    if receiveFile.content_type in imageMimeType: #image received
                        stillImg = np.fromfile(receiveFile, np.uint8)
                        stillImg = cv2.imdecode(stillImg, cv2.IMREAD_COLOR)
                    
                    elif receiveFile.content_type == "application/octet-stream": #dICOM+ received
                        stillImg = pydicom_custom.convert_file(receiveFile.stream)
                                          
                    else : #non-target received
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching content_type")
                        
                        if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                            if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                                Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"605",method)
                                return {"status":605,"transactionId":transactionId}

                            elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                                Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"605",method)
                                return {"status":605,"transactionId":transactionId}

                            elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                                Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"605",method)
                                return {"status":605,"transactionId":transactionId}

                        else:
                            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"605",method)
                            return {"status":605,"transactionId":transactionId}

                except:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiveing file error")

                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return {"status":603,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return {"status":603,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return {"status":603,"transactionId":transactionId}

                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"603",method)
                        return {"status":603,"transactionId":transactionId}

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    Log.make_log(f"request == async , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                    if Message_IF.serviceConfig["actionTarget"]["connectType"] != "async":
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async")

                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                            return {"status":604,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                            return {"status":604,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                            return {"status":604,"transactionId":transactionId}

                        else:
                            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                            return {"status":604,"transactionId":transactionId}

                try:
                    deviceId = request.headers['deviceId']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")

                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return {"status":601,"transactionId":transactionId}

                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                        return {"status":601,"transactionId":transactionId}
                    
                
                try:
                    requestToken = request.headers['token']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reveiving token fail")
                    
                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return {"status":601,"transactionId":transactionId}

                    else:
                        result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"601",method)
                        return {"status":601,"transactionId":transactionId}

                if templateType == "A":
                    stillImg = cv2.imencode('.jpg', stillImg)[1].tobytes()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                processingTh = threading.Thread(target=CommonTemplate.async_inference_func_still,
                                                args=(stillImg,requestToken,deviceId,transactionId,receiveTime,method,json.dumps(extraInfo),receiveFile.content_type)
                                                )
                processingTh.start()
                
                return {"status":200,"transactionId":transactionId}
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage))
            
            try:  
                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method) 
                        return {"status":500,"transactionId":transactionId}

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return {"status":500,"transactionId":transactionId}

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return {"status":500,"transactionId":transactionId}

                else:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                    return {"status":500,"transactionId":transactionId}
            except:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                return {"status":500,"transactionId":transactionId}

#endregion

#region single file upload(video)
@api.route('/visionai/asyncVideo')
class upload_asyncfile_video(Resource):
    def post(self):
        try:
            Log.make_log(f"threads count : {threading.active_count()}")
            global tempList
            global templateType
            extraInfo = {}
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            videoImg = []
            if request.method == 'POST':
                receiveTime = datetime.datetime.utcnow()

                transactionId = str(int(time.time()*1000000))[-11:]
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InferenceCall","START","")
                method= "REST"
                imageMimeType = ["video/x-msvideo","video/mpeg","video/ogg","video/webm","video/mp4"]
                Log.return_log_for_REST(request)
                try:
                    receiveFile = request.files['file']
                    Log.make_log(f"File content_type = {receiveFile.content_type}")
                    if receiveFile.content_type not in imageMimeType:
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching content_type")
                        
                        if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                            if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                                Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"605",method)
                                return {"status":605,"transactionId":transactionId}

                            elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                                Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"605",method)

                                return {"status":605,"transactionId":transactionId}

                            elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                                Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"605",method)
                                return {"status":605,"transactionId":transactionId}

                        else:
                            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"605",method)
                            return {"status":605,"transactionId":transactionId}

                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"data received","video","")
                    fileName="temp_file/"+f"{transactionId}"+secure_filename(receiveFile.filename)
                    receiveFile.save(fileName)
                    videoPath = fileName
                    cap = cv2.VideoCapture(videoPath)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"data save and load","video","")
                    #able add
                    extraInfo["fps"] = cap.get(cv2.CAP_PROP_FPS)
                except:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                    
                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            os.remove(videoPath)
                            return {"status":603,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            os.remove(videoPath)
                            return {"status":603,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            os.remove(videoPath)
                            return {"status":603,"transactionId":transactionId}

                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"603",method)
                        os.remove(videoPath)
                        return {"status":603,"transactionId":transactionId}

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    Log.make_log(f"request == async , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                    if Message_IF.serviceConfig["actionTarget"]["connectType"] != "async":
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                        
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                            return {"status":604,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                            return {"status":604,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                            return {"status":604,"transactionId":transactionId}

                        else:
                            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                            return {"status":604,"transactionId":transactionId}
                
                try:
                    deviceId = request.headers['deviceId']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")
                    
                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            os.remove(videoPath)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            os.remove(videoPath)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            os.remove(videoPath)
                            return {"status":601,"transactionId":transactionId}

                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                        os.remove(videoPath)
                        return {"status":601,"transactionId":transactionId}
                
                try:
                    requestToken = request.headers['token']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reveiving token fail")

                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            os.remove(videoPath)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            os.remove(videoPath)
                            return {"status":601,"transactionId":transactionId}

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            os.remove(videoPath)
                            return {"status":601,"transactionId":transactionId}

                    else:
                        Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],"601",method)
                        os.remove(videoPath)
                        return {"status":601,"transactionId":transactionId}

                while True:
                    ret, img = cap.read()
                    if ret:
                        if templateType == "A":
                            img = cv2.imencode('.jpg', img)[1].tobytes()
                        videoImg.append(img)
                    else:
                        break
                cap.release()
                if os.path.isfile(fileName):
                    tempList.append(fileName)
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                processingTh = threading.Thread(target=CommonTemplate.async_inference_func_video,
                                                args=(videoImg,requestToken,deviceId,transactionId,receiveTime,method,json.dumps(extraInfo),receiveFile.content_type)
                                                )
                processingTh.start()
                os.remove(videoPath)
                
                return {"status":200,"transactionId":transactionId}
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage)) 
            if os.path.isfile(fileName):
                    tempList.append(fileName)
            try: 
                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)

                else:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                try:
                    os.remove(videoPath)
                except:
                    pass
                return {"status":500,"transactionId":transactionId}
            except:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                return {"status":500,"transactionId":transactionId}
#endregion

#region single file upload sync Still(json)
@api.route('/visionai/syncStillImage')
class upload_syncfile_image(Resource):
    def post(self):
        try:
            Log.make_log(f"threads count : {threading.active_count()}")
            global templateType
            extraInfo = {}
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            if request.method == 'POST':
                receiveTime = datetime.datetime.utcnow()
                method= "REST"
                transactionId = str(int(time.time()*1000000))[-11:]
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InferenceCall","START","")
                imageMimeType = ["image/png","image/jpeg","image/bmp","image/webp"]
                Log.return_log_for_REST(request)
                try:
                    receiveFile = request.files['file']
                    Log.make_log(f"File content_type = {receiveFile.content_type}")
                    if receiveFile.content_type in imageMimeType:
                        stillImg = np.fromfile(receiveFile, np.uint8)
                        stillImg = cv2.imdecode(stillImg, cv2.IMREAD_COLOR)

                    elif receiveFile.content_type == "application/octet-stream": #dICOM received
                        stillImg = pydicom_custom.convert_file(receiveFile.stream)

                    else: 
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching content_type")
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"605",method)
                        resp = make_response(json.dumps(result))
                        resp.headers['Access-Control-Allow-Origin'] = "*"
                        return resp


                except:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"603",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    Log.make_log(f"request == sync , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                    if Message_IF.serviceConfig["actionTarget"]["connectType"] != "sync":
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async")
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                        resp = make_response(json.dumps(result))
                        resp.headers['Access-Control-Allow-Origin'] = "*"
                        return resp
                else:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp

                try:
                    deviceId = request.headers['deviceId']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp
                
                try:
                    requestToken = request.headers['token']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reveiving token fail")
                    result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"601",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp

                if templateType =="A":
                    stillImg = cv2.imencode('.jpg', stillImg)[1].tobytes()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                _, result = CommonTemplate.sync_inference_func_still(stillImg,requestToken,deviceId,transactionId,receiveTime,method,json.dumps(extraInfo),receiveFile.content_type)

                resp = make_response(json.dumps(result))
                resp.headers['Access-Control-Allow-Origin'] = "*"
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS","")
                return resp

        except Exception as errorMessage:
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage))
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method) 
            resp = make_response(json.dumps(result))
            resp.headers['Access-Control-Allow-Origin'] = "*"
            return resp

#endregion

@api.route('/visionai/syncVideo')
class upload_asyncfile_video(Resource):
    def post(self):
        try:
            Log.make_log(f"threads count : {threading.active_count()}")
            
            global tempList
            global templateType
            extraInfo = {}
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            videoImg = []
            if request.method == 'POST':
                receiveTime = datetime.datetime.utcnow()

                transactionId = str(int(time.time()*1000000))[-11:]
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InferenceCall","START","")
                method= "REST"
                imageMimeType = ["video/x-msvideo","video/mpeg","video/ogg","video/webm","video/mp4"]
                Log.return_log_for_REST(request)
                try:
                    receiveFile = request.files['file']
                    Log.make_log(f"File content_type = {receiveFile.content_type}")
                    if receiveFile.content_type not in imageMimeType:
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching content_type")
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"605",method)
                        resp = make_response(json.dumps(result))
                        resp.headers['Access-Control-Allow-Origin'] = "*"
                        return resp
                    fileName="temp_file/"+f"{transactionId}"+secure_filename(receiveFile.filename)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"data received","video","")
                    receiveFile.save(fileName)
                    videoPath = fileName
                    cap = cv2.VideoCapture(videoPath)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"data save and load","video","")
                    #able add
                    extraInfo["fps"] = cap.get(cv2.CAP_PROP_FPS)
                except:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"605",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    Log.make_log(f"request == sync , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                    if Message_IF.serviceConfig["actionTarget"]["connectType"] != "sync":
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                        resp = make_response(json.dumps(result))
                        resp.headers['Access-Control-Allow-Origin'] = "*"
                        return resp

                else:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp
                
                try:
                    deviceId = request.headers['deviceId']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp
                
                try:
                    requestToken = request.headers['token']
                except KeyError:
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reveiving token fail")
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    resp = make_response(json.dumps(result))
                    resp.headers['Access-Control-Allow-Origin'] = "*"
                    return resp

                while True:
                    ret, img = cap.read()
                    if ret:
                        if templateType == "A":
                            img = cv2.imencode('.jpg', img)[1].tobytes()
                        videoImg.append(img)
                    else:
                        break
                cap.release()
                if os.path.isfile(fileName):
                    tempList.append(fileName)
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                _, result=CommonTemplate.sync_inference_func_video(videoImg,requestToken,deviceId,transactionId,receiveTime,method,json.dumps(extraInfo),receiveFile.content_type)
                del videoImg
                resp = make_response(json.dumps(result))
                resp.headers['Access-Control-Allow-Origin'] = "*"
                
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS","")
                return resp

        except Exception as errorMessage:
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage))
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            if os.path.isfile(fileName):
                tempList.append(fileName)
            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method) 
            resp = make_response(json.dumps(result))
            resp.headers['Access-Control-Allow-Origin'] = "*"
            return resp


def flask_server():
    threading.Thread(target=remove_tempFile).start()
    app.run( host=f"{serverInfo['CTRESTAPI']['address']}", port=int(serverInfo['CTRESTAPI']['port']))

if __name__ == "__main__":
    flask_server()

