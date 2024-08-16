import re
import numpy as np
import grpc
import cv2
import time
import configparser
import threading
import datetime

import Message_IF
import Output_interface
import Log
import os
import pydicom_custom
import io
import json
from python_pb import Interface_pb2_grpc
from python_pb import Interface_pb2
from concurrent import futures

templateType=""

#region Global Variables
imgListDict = {}
imgProcessNum = 1
#endregion

#region read ini
serverInfo= configparser.ConfigParser()
serverInfo.read('Server_info.ini')
#endregion

def convertType(resultList) :
    if str(type(resultList)) != "<class 'list'>" :
        return [resultList]

    return resultList


batchQueue = list()   

timeoutCnt = 10
timeoutflag = False

def timeoutChecker (requestToken,deviceId,transactionId,receiveTime,method,extraInfo,mimeType) :
    global timeoutCnt
    global timeoutflag
    
    while timeoutCnt > 0 :
        timeoutCnt = timeoutCnt - 1
        time.sleep(1)
        Log.make_log(timeoutCnt)
        if timeoutflag is False :
            return

    Log.make_log('Time Out')
    timeoutflag = False

    if serverInfo['BatchMode']['isDynamic'] == 'True' :
        batchImgList = []
        firstBatch = True
        while(batchQueue) :
            batchData = batchQueue.pop(0)
            if firstBatch : #first Time
                receiveTime = batchData[1]
                firstBatch = False
            batchImg=batchData[0]
            batchImgList.append(batchImg)

        import CommonTemplateB as CommonTemplate  

        processingTh = threading.Thread(target=CommonTemplate.async_inference_func_batch,
                                args=(batchImgList,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,mimeType)
                                )
        processingTh.start()
    else : 
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reseiving file Time Out")
        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
            Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)

        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
            Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)

        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
            Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
        batchQueue.clear()


def timerStart(requestToken,deviceId,transactionId,receiveTime,method,extraInfo,mimeType) : 
    global timeoutCnt
    global timeoutflag
    timeoutCnt = int(serverInfo['BatchMode']['timeOutCount'])
    timeoutflag = True
    timeTh = threading.Thread(target=timeoutChecker,args=(requestToken,deviceId,transactionId,receiveTime,method,extraInfo,mimeType))
    timeTh.start()
    return

def timerStop() : 
    global timeoutflag
    global timeoutCnt
    timeoutflag = False
    timeoutCnt = int(serverInfo['BatchMode']['timeOutCount'])
    return

def timerReflash() : 
    global timeoutCnt
    timeoutCnt = int(serverInfo['BatchMode']['timeOutCount'])
    return

class Interface_gRPC(Interface_pb2_grpc.Image_DetectServicer):
    #region image file taker

    def async_still_image(self, request, context):
        try:
            global templateType
            global batchQueue
            
            Log.request_log_for_gRPC(request)
            extraInfo = request.extraInfo

            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate            

            method= "gRPC"
            receiveTime = datetime.datetime.utcnow()
            transactionId = str(int(time.time()*1000000))[-11:]
            
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                Log.make_log(f"request == async , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                if Message_IF.serviceConfig["actionTarget"]["connectType"] != "async":
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                    
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)

                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)

            try:
                deviceId = request.deviceId
                1/len(deviceId) 
            except ZeroDivisionError:
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving deviceId fail")

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                else:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    return Interface_pb2.asyncReply(status='601',transactionId=transactionId)
            
            try:
                requestToken = request.token
                1/len(requestToken)
            except ZeroDivisionError:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reseiving token fail")

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reseiving token fail")
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reseiving token fail")
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                else:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving token fail")
                    return Interface_pb2.asyncReply(status='601',transactionId=transactionId)
            
            try:
                stillImg = request.file
                1/len(stillImg)
            except :
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")

                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                else:
                    result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                    return Interface_pb2.asyncReply(status='603',transactionId=transactionId)
                
            try:
                Log.make_log(f"File mimeType = {request.mimeType}")
                if request.mimeType == "application/dicom":
                    stillImg = io.BytesIO(stillImg)
                    stillImg = pydicom_custom.convert_file(stillImg)
                    stillImg = cv2.imencode('.jpg', stillImg)[1].tobytes()
            except:
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error(mimeTypee)")
                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                else:
                    result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                    return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

            if templateType == "B":
                try:
                    encodedImg = np.fromstring(stillImg, dtype = np.uint8)
                    stillImg = np.array(cv2.imdecode(encodedImg, cv2.IMREAD_UNCHANGED))
                except:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                    else:
                        result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving file error")
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

            if serverInfo['BatchMode']['batch'] == 'True':

                if timeoutflag :
                    timerReflash()
                else :
                    timerStart(requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)

                batchQueue.append([stillImg,receiveTime])
                batchSize = int(serverInfo['BatchMode']['batchSize'])
                
                if len(batchQueue)>=batchSize:
                    batchImgList=list()
                    for batchCount in range(batchSize):
                        batchData = batchQueue.pop(0)
                        if batchCount == 0 : #first Time
                            receiveTime = batchData[1]
                            
                        #if batchCount == batchSize - 1 : #Last Time
                        #    pass
                        
                        batchImg=batchData[0]
                        batchImgList.append(batchImg)
                        
                    #send
                    timerStop()
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                    processingTh = threading.Thread(target=CommonTemplate.async_inference_func_batch,
                                            args=(batchImgList,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)
                                            )
                    processingTh.start()

                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","Batch Received")

            else:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                processingTh = threading.Thread(target=CommonTemplate.async_inference_func_still,
                                                args=(stillImg,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)
                                                )
                processingTh.start()
                

            return Interface_pb2.asyncReply(status='200',transactionId=transactionId)
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage)) 
            try:
                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return Interface_pb2.asyncReply(status='500',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return Interface_pb2.asyncReply(status='500',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return Interface_pb2.asyncReply(status='500',transactionId=transactionId)

                else:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                    return Interface_pb2.asyncReply(status='500',transactionId=transactionId)
            except:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                return Interface_pb2.asyncReply(status='500',transactionId=transactionId)
    #endregion

    #region video file taker
    def async_video(self, request_iterator, context):
        try:
            global templateType

            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            method = "gRPC"
            receiveTime = datetime.datetime.utcnow()
            transactionId = str(int(time.time()*1000000))[-11:]
            videoImg = []
            requestToken = ''
            deviceId = ''
            
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                Log.make_log(f"request == async , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                if Message_IF.serviceConfig["actionTarget"]["connectType"] != "async":
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                    
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"604",method)
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)
                        
                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                        return Interface_pb2.asyncReply(status='604',transactionId=transactionId)
                    

            for request in request_iterator:
                Log.request_log_for_gRPC(request)
                extraInfo = request.extraInfo

                try:
                    deviceId = request.deviceId
                    1/len(deviceId)
                except ZeroDivisionError:
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")

                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return Interface_pb2.asyncReply(restatusp='601',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")
                            return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reveiving deviceId fail")
                            return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                    else:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)
                
                try:
                    requestToken = request.token
                    1/len(requestToken)
                except ZeroDivisionError:
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reveiving token fail")
                    
                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"601",method)
                            return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                    else:
                        result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"601",method)
                        return Interface_pb2.asyncReply(status='601',transactionId=transactionId)

                try:
                    stillImg = request.file
                    1/len(stillImg)
                except :
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                    if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                        if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                            Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                            Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                        elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                            Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                    else:
                        result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                        return Interface_pb2.asyncReply(status='603',transactionId=transactionId)
                        
                if templateType == "B":
                    try:
                        encoded_img = np.fromstring(stillImg, dtype = np.uint8)
                        stillImg = np.array(cv2.imdecode(encoded_img, cv2.IMREAD_UNCHANGED))
                    except:
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                        
                        if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                            if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                                Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                                return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                            elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                                Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                                return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                            elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                                Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"603",method)
                                return Interface_pb2.asyncReply(status='603',transactionId=transactionId)

                        else:
                            result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                            return Interface_pb2.asyncReply(status='603',transactionId=transactionId)
                
                if serverInfo['BatchMode']['batch'] != 'True':
                    if timeoutflag :
                        timerReflash()
                    else :
                        timerStart(requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)

                    if len(batchQueue) > 0:
                        batchSize = int(serverInfo['BatchMode']['batchSize'])
                        batchQueue.append([stillImg,receiveTime])
                        
                        if len(batchQueue)>=batchSize:
                            batchImgList=list()
                            for batchCount in range(batchSize):
                                batchData = batchQueue.pop(0)
                                if batchCount == 0 : #first Time
                                    receiveTime = batchData[1]
                                    
                                #if batchCount == batchSize - 1 : #Last Time
                                #    pass
                                
                                batchImg=batchData[0]
                                batchImgList.append(batchImg)
                                
                            #send
                            timerStop()
                            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                            processingTh = threading.Thread(target=CommonTemplate.async_inference_func_batch,
                                                    args=(batchImgList,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)
                                                    )
                            processingTh.start()
                        
                    else:
                        batchQueue.append([stillImg,receiveTime])
                    Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","Batch Received")

                else : #not Batch
                    videoImg.append(stillImg)

            if serverInfo['BatchMode']['batch'] != 'True':
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
                processingTh = threading.Thread(target=CommonTemplate.async_inference_func_video,
                                                args=(videoImg,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)
                                                )
                processingTh.start()
            return Interface_pb2.asyncReply(status='200',transactionId=transactionId)
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage)) 
            
            try:
                if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                    if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                        Output_interface.error_output_REST(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return Interface_pb2.asyncReply(status='500',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                        Output_interface.error_output_gRPC(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return Interface_pb2.asyncReply(status='500',transactionId=transactionId)

                    elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                        Output_interface.error_output_ftp(None,"",transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                        return Interface_pb2.asyncReply(status='500',transactionId=transactionId)

                else:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                    return Interface_pb2.asyncReply(status='500',transactionId=transactionId)
            except:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
                return Interface_pb2.asyncReply(status='500',transactionId=transactionId)
    #endregion

    #region image file taker(sync mode)
    def sync_still_image(self, request, context):
        try:
            global templateType
            extraInfo = request.extraInfo
            Log.request_log_for_gRPC(request)
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            method = "gRPC"
            receiveTime = datetime.datetime.utcnow()
            transactionId = str(int(time.time()*1000000))[-11:]

            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                Log.make_log(f"request == sync , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                if Message_IF.serviceConfig["actionTarget"]["connectType"] != "sync":
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                    return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="604")
            else:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                           sendTime=result["sendTime"],processingTime=result["processingTime"],
                                           transactionId=result["transactionId"],result=str(result["result"]),status="604")

            try:
                deviceId = request.deviceId
                1/len(deviceId)
            except ZeroDivisionError:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving deviceId fail")
                return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="601")

            try:
                requestToken = request.token
                1/len(requestToken)
            except ZeroDivisionError:
                result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"601",method)
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","FAIL","reseiving token fail")
                return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="601")

            try:
                stillImg = request.file
                1/len(stillImg)
            except :
                result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="603")
            try:
                Log.make_log(f"File mimeType = {request.mimeType}")
                if request.mimeType == "application/dicom":
                    stillImg = io.BytesIO(stillImg)
                    stillImg = pydicom_custom.convert_file(stillImg)
                    stillImg = cv2.imencode('.jpg', stillImg)[1].tobytes()
            except:
                result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error(mimeTypee)")
                return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="603")
            
            if templateType == "B":
                try:
                    encodedImg = np.fromstring(stillImg, dtype = np.uint8)
                    stillImg = np.array(cv2.imdecode(encodedImg, cv2.IMREAD_UNCHANGED))
                except:
                    result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"603",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                    return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="603")

            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
            resultImg, result = CommonTemplate.sync_inference_func_still(stillImg,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)
            try:
                resultImg = resultImg.tobytes()
            except:
                pass

            
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS","")
            return Interface_pb2.syncReply(image=resultImg,deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                           sendTime=result["sendTime"],processingTime=result["processingTime"],
                                           transactionId=result["transactionId"],result=str(result["result"]),status=result['status'])
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage)) 
            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
            return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                           sendTime=result["sendTime"],processingTime=result["processingTime"],
                                           transactionId=result["transactionId"],result=str(result["result"]),status=result['status'])
    #endregion

    #region sync video file taker
    def sync_video(self, request_iterator, context):
        try:
            global templateType

            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            method = "gRPC"
            receiveTime = datetime.datetime.utcnow()
            transactionId = str(int(time.time()*1000000))[-11:]
            videoImg = []
            requestToken = ''
            deviceId = ''
            
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                Log.make_log(f"request == sync , config == {Message_IF.serviceConfig['actionTarget']['connectType']}")
                if Message_IF.serviceConfig["actionTarget"]["connectType"] != "sync":
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                    return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="604")
            else:
                result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"604",method)
                Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","no matching sync/async") 
                return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                           sendTime=result["sendTime"],processingTime=result["processingTime"],
                                           transactionId=result["transactionId"],result=str(result["result"]),status="604")
                    
            for request in request_iterator:
                Log.request_log_for_gRPC(request)
                extraInfo = request.extraInfo
                
                try:
                    deviceId = request.deviceId
                    1/len(deviceId)
                except ZeroDivisionError:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving deviceId fail")
                    return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="601")

                try:
                    requestToken = request.token
                    1/len(requestToken)
                except ZeroDivisionError:
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"601",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving token fail")
                    return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status="601")

                try:
                    stillImg = request.file
                    1/len(stillImg)
                except :
                    result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"603",method)
                    Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                    return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                                    sendTime=result["sendTime"],processingTime=result["processingTime"],
                                                    transactionId=result["transactionId"],result=str(result["result"]),status="603")
                        
                if templateType == "B":
                    try:
                        encoded_img = np.fromstring(stillImg, dtype = np.uint8)
                        stillImg = np.array(cv2.imdecode(encoded_img, cv2.IMREAD_UNCHANGED))
                    except:
                        result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"603",method)
                        Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL","reseiving file error")
                        return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                                        sendTime=result["sendTime"],processingTime=result["processingTime"],
                                                        transactionId=result["transactionId"],result=str(result["result"]),status="603")

                videoImg.append(stillImg)

            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"InputInterface","PASS","")
            resultImg,result = CommonTemplate.sync_inference_func_video(videoImg,requestToken,deviceId,transactionId,receiveTime,method,extraInfo,request.mimeType)
            try:
                resultImg = resultImg.tobytes()
            except:
                pass

            
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS","")
            return Interface_pb2.syncReply(image=resultImg,deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                           sendTime=result["sendTime"],processingTime=result["processingTime"],
                                           transactionId=result["transactionId"],result=str(result["result"]),status=result['status'])
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            Log.processing_log(os.environ.get("AiServiceId"),"",transactionId,"InputInterface","FAIL",str(errorMessage)) 
            result = Output_interface.error_output_sync(None,"",transactionId,receiveTime,[],"500",method)
            return Interface_pb2.syncReply(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                           sendTime=result["sendTime"],processingTime=result["processingTime"],
                                           transactionId=result["transactionId"],result=str(result["result"]),status=result['status'])
    #endregion

    #region image async still external return receive(external async mode)
    def async_still_external_return_receive(self, request, context):
        try:
            global templateType
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            deviceId = request.deviceId
            transactionId = request.transactionId
            receiveTime = datetime.datetime.strptime(request.receiveTime,'%Y-%m-%d %H:%M:%S.%f')
            result = eval(request.result)
            result = convertType(result)
            status = request.status
            method = request.method
            resultImg = np.fromstring(request.image, dtype = np.uint8)
            resultImg = np.array(cv2.imdecode(resultImg, cv2.IMREAD_UNCHANGED))
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inference","PASS",str(result))
            processingTh = threading.Thread(target=CommonTemplate.async_external_still_output,
                                            args=(resultImg,deviceId,transactionId,receiveTime,result,status,method)
                                            )
            processingTh.start()
            return Interface_pb2.asyncReply(status='200')
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)

                return Interface_pb2.asyncReply(status='501')
            else:
                result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"501",method)
                return Interface_pb2.asyncReply(status='501')

    #endregion

    #region image async video external return receive(external async mode)
    def async_video_external_return_receive(self, request, context):
        try:
            global templateType
            if templateType == 'A':
                import CommonTemplateA_Mgmt as CommonTemplate
            elif  templateType == 'B':
                import CommonTemplateB as CommonTemplate
            deviceId = request.deviceId
            transactionId = request.transactionId
            receiveTime = datetime.datetime.strptime(request.receiveTime,'%Y-%m-%d %H:%M:%S.%f')
            result = eval(request.result)
            result = convertType(result)
            status = request.status
            method = request.method
            resultImg = np.fromstring(request.image, dtype = np.uint8)
            resultImg = np.array(cv2.imdecode(resultImg, cv2.IMREAD_UNCHANGED))
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inference","PASS",str(result))
            processingTh = threading.Thread(target=CommonTemplate.async_external_video_output,
                                            args=(resultImg,deviceId,transactionId,receiveTime,result,status,method)
                                            )
            processingTh.start()
            return Interface_pb2.asyncReply(status='200')
        except Exception as errorMessage:
            Log.make_error_log(errorMessage)
            Log.make_trace_error_log()
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,deviceId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)

                return Interface_pb2.asyncReply(status='501')
            else:
                result = Output_interface.error_output_sync(None,deviceId,transactionId,receiveTime,[],"501",method)
                return Interface_pb2.asyncReply(status='501')
            
    #endregion

#region main gRPC server
def main_gRPC_serve():

    MAX_MESSAGE_LENGTH = 1000*1024*1024
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options = [
        ('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
        ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)
    ])
    Interface_pb2_grpc.add_Image_DetectServicer_to_server(Interface_gRPC(),server)
    server.add_insecure_port(f"{serverInfo['CTgRPC']['address']}:{serverInfo['CTgRPC']['port']}")
    server.start()
    server.wait_for_termination()
#endregion

if __name__=="__main__":
    main_gRPC_serve()
