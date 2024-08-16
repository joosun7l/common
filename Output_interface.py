import json
import requests
import grpc
import configparser
import cv2
import datetime
import Log
import os
import numpy as np
from threading import Thread
from ftplib import FTP
from python_pb import Output_pb2
from python_pb import Output_pb2_grpc
from python_pb import Interface_pb2
from python_pb import Interface_pb2_grpc
from python_pb import InferenceResult_pb2
from python_pb import InferenceResult_pb2_grpc

#region read ini
serverInfo= configparser.ConfigParser()
serverInfo.read('Server_info.ini')
#endregion

#region time to millisecond
def to_millisecond(time):
    splitTime = str(time).split(":")
    hTime = int(splitTime[0])*3600*1000
    mTime = int(splitTime[1])*60*1000
    sTime = round(float(splitTime[2]),3)*1000
    return hTime+mTime+int(sTime)
#endregion

#region send inferenceInfo
def send_inferenceInfo(resultImg,result):
    if serverInfo['inferenceInfo']['isSend'] == '1':
        if resultImg is not None:
            # resultImg = cv2.imencode('.jpg', resultImg)[1]
            channel = grpc.insecure_channel(f"{serverInfo['inferenceInfo']['address']}:{serverInfo['inferenceInfo']['port']}")
            stub = InferenceResult_pb2_grpc.InferenceResultStub(channel)
            response = stub.inference_result(InferenceResult_pb2.inferenceResultRequest(file=resultImg.tobytes(),originFileName="inferenceResult.jpg",json=json.dumps(result)))
        else:
            channel = grpc.insecure_channel(f"{serverInfo['inferenceInfo']['address']}:{serverInfo['inferenceInfo']['port']}")
            stub = InferenceResult_pb2_grpc.InferenceResultStub(channel)
            response = stub.inference_result(InferenceResult_pb2.inferenceResultRequest(originFileName="inferenceResult.jpg",json=json.dumps(result)))
#endregion

#region send inferenceInfo
def send_inferenceInfo_by_RESTAPI(resultImg,result):
    if serverInfo['inferenceInfo']['isSend'] == '1':
        if resultImg is not None:
            # resultImg = cv2.imencode('.jpg', resultImg)[1]
            resp = requests.request("POST",f"http://{serverInfo['inferenceInfo']['address']}:{serverInfo['inferenceInfo']['port']}/visionai/inferenceInfo",files=[("file",('transactionImage.jpg',resultImg,'image/jpeg'))],data={'json':json.dumps(result)})
        else:
            resultImg = np.zeros((512,512,3),np.uint8)
            resultImg = cv2.imencode('.jpg', resultImg)[1]
            resp = requests.request("POST",f"http://{serverInfo['inferenceInfo']['address']}:{serverInfo['inferenceInfo']['port']}/visionai/inferenceInfo",files=[("file",('transactionImage.jpg',resultImg,'image/jpeg'))],data={'json':json.dumps(result)})
            #resp = requests.request("POST",f"http://{serverInfo['inferenceInfo']['address']}:{serverInfo['inferenceInfo']['port']}/visionai/inferenceInfo",headers={"Content-Type":"multipart/form-data"},data={'json':json.dumps(result)})
#endregion

#region common output data making & send inferenceInfo
def common_output(deviceId,transactionId,receiveTime,resultList,status,method):
    sendTime = datetime.datetime.utcnow() 
    result = {
        "status" : status,
        "method" : method,
        "message" : "message",
        "aiServiceId" : f'{os.environ.get("AiServiceId")}',
        "deviceId" : deviceId,
        "receiveTime" : str(receiveTime.strftime('%Y-%m-%dT%H:%M:%S.%f'))[:-3]+'+00:00',
        "sendTime" : str(sendTime.strftime('%Y-%m-%dT%H:%M:%S.%f'))[:-3]+'+00:00',
        "processingTime" : str(to_millisecond(sendTime - receiveTime)),
        "transactionId" : transactionId,
        "result" : resultList
    }
    return result

#region RESTAPI asyncStillImage output
def output_REST_async(resultImg,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)
    resultImg = cv2.imencode('.jpg', resultImg)[1]
    try:
        resp = requests.request("POST",config['actionTarget']['endpoint'][ 'location'],files=[("file",('transactionImage.jpg',resultImg,'image/jpeg'))],data={'json':json.dumps(result)})
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
    except:
        result["status"] = "403"
    try:
        infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
        infoThread.daemon=True
        infoThread.start()
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
    except:
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
        pass
#endregion

#region gRPC async_still output
def output_gRPC_async(resultImg,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)
    resultImg = cv2.imencode('.jpg', resultImg)[1]
    
    try:
        channel = grpc.insecure_channel(config['actionTarget']['endpoint'][ 'location'])
        stub = Output_pb2_grpc.Send_outputStub(channel)
        response = stub.send_async_still(Output_pb2.outputInfo(image=resultImg.tobytes(),deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status=status))
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
    except:
        result["status"] = "403"
    try:
        infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
        infoThread.daemon=True
        infoThread.start()
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
    except:
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
        pass
#endregion

#region ftp async_still output
def output_ftp_async(resultImg,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)

    imgPath = f"temp_file/temp_result_{transactionId}.jpg"
    txtPath = f"temp_file/temp_result_{transactionId}.txt"

    cv2.imwrite(imgPath,resultImg)

    with open(txtPath, "w") as txt_file:
        txt_file.write(json.dumps(result))

    resultImg = cv2.imencode('.jpg', resultImg)[1]
    
    try:
        ftp = FTP()
        ftpAdress=config["actionTarget"]["endpoint"]["location"].split(":")
        ftp.connect(ftpAdress[0], int(ftpAdress[1]))
        ftp.login(config["actionTarget"]["endpoint"]["id"], config["actionTarget"]["endpoint"]["password"])
        ftp.cwd("./upload")

        with open(imgPath,"rb") as imgFile:
            ftp.storbinary(f"STOR {transactionId}.jpg",imgFile)
        with open(txtPath, 'rb') as txt_file :
            ftp.storbinary(f"STOR {transactionId}.txt",txt_file)

        os.remove(imgPath)
        os.remove(txtPath)
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
    except:
        if os.path.isfile(imgPath):
            os.remove(imgPath)
        if os.path.isfile(txtPath):
            os.remove(txtPath)
        result["status"] = "403"
    try:
        infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
        infoThread.daemon=True
        infoThread.start()
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
    except:
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
        pass
#endregion

#region gRPC async_still output serial
def output_gRPC_serial(resultImg,token,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)
    resultImg = cv2.imencode('.jpg', resultImg)[1]
    channel = grpc.insecure_channel(config['workflow']['grpc'])
    stub = Interface_pb2_grpc.Image_DetectStub(channel)
    try:
        response = stub.async_still_image(Interface_pb2.imageRequest(file=resultImg.tobytes(),deviceId=deviceId,token=token,extraInfo=str(resultList)))
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
    except:
        result["status"] = "403"
    try:
        infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
        infoThread.daemon=True
        infoThread.start()
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
    except:
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
        pass
#endregion

def error_output_REST(resultImg,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)
    if resultImg is not None:
        resultImg = cv2.imencode('.jpg', resultImg)[1]
        try:
            resp = requests.request("POST",config['actionTarget']['endpoint'][ 'location'],files=[("file",('transactionImage.jpg',resultImg,'image/jpeg'))],data={'json':json.dumps(result)})
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
        except:
            pass
        try:
            infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
            infoThread.daemon=True
            infoThread.start()
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
        except:
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
            pass
    else:
        try:
            resultImg = np.zeros((512,512,3),np.uint8)
            resultImg = cv2.imencode('.jpg', resultImg)[1]
            resp = requests.request("POST",config['actionTarget']['endpoint'][ 'location'],files=[("file",('transactionImage.jpg',resultImg,'image/jpeg'))],data={'json':json.dumps(result)})
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
            # resp = requests.request("POST",config['actionTarget']['endpoint'][ 'location'],headers={"Content-Type":"multipart/form-data;"},data={'json':json.dumps(result)})
        except:
            try:
                infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
                infoThread.daemon=True
                infoThread.start()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
            except:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
                pass
        try:
            infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
            infoThread.daemon=True
            infoThread.start()
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
        except:
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
            pass

def error_output_gRPC(resultImg,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)
    if resultImg is not None:
        resultImg = cv2.imencode('.jpg', resultImg)[1]
        try:
            channel = grpc.insecure_channel(config['actionTarget']['endpoint'][ 'location'])
            stub = Output_pb2_grpc.Send_outputStub(channel)
            response = stub.send_async_still(Output_pb2.outputInfo(image=resultImg.tobytes(),deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status=status))
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
        except:
            try:
                infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
                infoThread.daemon=True
                infoThread.start()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
            except:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
                pass
    else:
        try:
            channel = grpc.insecure_channel(config['actionTarget']['endpoint'][ 'location'])
            stub = Output_pb2_grpc.Send_outputStub(channel)
            response = stub.send_async_still(Output_pb2.outputInfo(deviceId=result["deviceId"],receiveTime=result["receiveTime"],
                                               sendTime=result["sendTime"],processingTime=result["processingTime"],
                                               transactionId=result["transactionId"],result=str(result["result"]),status=status))
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
        except:
            try:
                infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
                infoThread.daemon=True
                infoThread.start()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
                return 1
            except:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
                return 1
        try:
            infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
            infoThread.daemon=True
            infoThread.start()
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
        except:
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
            pass

def error_output_ftp(resultImg,deviceId,transactionId,receiveTime,resultList,config,status,method):
    result = common_output(deviceId,transactionId,receiveTime,resultList,status,method)
    imgPath = f"temp_file/temp_result_{transactionId}.jpg"
    txtPath = f"temp_file/temp_result_{transactionId}.txt"
    if resultImg is not None:
        cv2.imwrite(imgPath,resultImg)

        with open(txtPath, "w") as txt_file:
            txt_file.write(json.dumps(result))
        resultImg = cv2.imencode('.jpg', resultImg)[1]
        try:
            ftp = FTP()
            ftpAdress=config["actionTarget"]["endpoint"]["location"].split(":")
            ftp.connect(ftpAdress[0], int(ftpAdress[1]))
            ftp.login(config["actionTarget"]["endpoint"]["id"], config["actionTarget"]["endpoint"]["password"])
            ftp.cwd("./upload")

            with open(imgPath,"rb") as imgFile:
                ftp.storbinary(f"STOR {transactionId}.jpg",imgFile)
            with open(txtPath, 'rb') as txt_file :
                ftp.storbinary(f"STOR {transactionId}.txt",txt_file)

            os.remove(imgPath)
            os.remove(txtPath)
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
        except:
            if os.path.isfile(imgPath):
                os.remove(imgPath)
            if os.path.isfile(txtPath):
                os.remove(txtPath)
            try:
                infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
                infoThread.daemon=True
                infoThread.start()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
            except:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
                pass
    else:
        with open(txtPath, "w") as txt_file:
            txt_file.write(json.dumps(result))
        try:
            ftp = FTP()
            ftpAdress=config["actionTarget"]["endpoint"]["location"].split(":")
            ftp.connect(ftpAdress[0], int(ftpAdress[1]))
            ftp.login(config["actionTarget"]["endpoint"]["id"], config["actionTarget"]["endpoint"]["password"])
            ftp.cwd("./upload")

            with open(txtPath, 'rb') as txt_file :
                ftp.storbinary(f"STOR {transactionId}.txt",txt_file)

            os.remove(imgPath)
            os.remove(txtPath)
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"OutputInterface","PASS",str(result))
        except:
            if os.path.isfile(imgPath):
                os.remove(imgPath)
            if os.path.isfile(txtPath):
                os.remove(txtPath)
                
            try:
                infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
                infoThread.daemon=True
                infoThread.start()
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
                return 1
            except:
                Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
                return 1
        try:
            infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
            infoThread.daemon=True
            infoThread.start()
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
        except:
            Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
            pass        

def error_output_sync(resultImg,deviceId,transactionId,receiveTime,resultList,status,method):
    if resultImg is not None:
        resultImg = cv2.imencode('.jpg', resultImg)[1]
    sendTime = datetime.datetime.utcnow() 
    result = {
        "status" : status,
        "deviceId" : deviceId,
        "method" : method,
        "message" : "message",
        "aiServiceId" : f'{os.environ.get("AiServiceId")}',
        "receiveTime" : str(receiveTime.strftime('%Y-%m-%dT%H:%M:%S.%f'))[:-3]+'+00:00',
        "sendTime" : str(sendTime.strftime('%Y-%m-%dT%H:%M:%S.%f'))[:-3]+'+00:00',
        "processingTime" : str(to_millisecond(sendTime - receiveTime)),
        "transactionId" : transactionId,
        "result" : resultList
    }
    try:
        infoThread=Thread(target=send_inferenceInfo,args=(resultImg,result))
        infoThread.daemon=True
        infoThread.start()
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","PASS",str(result))
    except:
        Log.processing_log(os.environ.get("AiServiceId"),deviceId,transactionId,"Inferenceinfo","FAIL",str(result))
        pass
    return result

