#CommonTemplate Type - A    Inference Docker's lib.
import Input_interface
import Output_interface
import numpy as np
import cv2
import Message_IF
import gRPC
import RESTAPI
import os
import Log
import copy
import traceback
from threading import Thread

gRPC.templateType = "A"
RESTAPI.templateType = "A"

def convertType(resultList) :
    if str(type(resultList)) != "<class 'list'>" :
        return [resultList]

    return resultList

def sync_inference_func_still(img,requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        workflow,status,statusMsg = Input_interface.service_check(img,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,"still",extraInfo,mimeType)
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","PASS","")
        if status == '200':
            pass
        else:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","FAIL",str(status+" "+statusMsg))
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
            return None, result

        try:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference start","PASS","")
            resultImg, resultList, status = Input_interface.sync_still_external_inference(img,extraInfo)
            resultList = convertType(resultList)
            if status == '200':
                pass
            else:
                Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error") 
                result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
                return None, result
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
            try:
                if resultImg == None:
                    resultImg=img
            except ValueError:
                pass
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            resultList = []
            status = '501'
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,resultList,status,method)
            return None, result

        encodedImg = np.fromstring(resultImg, dtype = np.uint8)
        resultImg = np.array(cv2.imdecode(encodedImg, cv2.IMREAD_UNCHANGED))
        if workflow == "serial":
            Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
        result = Output_interface.common_output(requestDevideId,transactionId,receiveTime,resultList,status,method)
        resultImg = cv2.imencode('.jpg', resultImg)[1]
        try:
            infoThread=Thread(target=Output_interface.send_inferenceInfo,args=(resultImg,result))
            infoThread.daemon=True
            infoThread.start()
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inferenceinfo","PASS",str(result))
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inferenceinfo","FAIL",str(result))
            pass
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inferenceinfo","PASS",str(result))
        return resultImg, result

    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()
        result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"500",method)
        return None, result

def sync_inference_func_video(imgList,requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        videoImgList = copy.copy(imgList)
        workflow,status,statusMsg = Input_interface.service_check(imgList,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,"video",extraInfo,mimeType)
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","PASS","")
        if status == '200':
            pass
        else:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","FAIL",str(status+" "+statusMsg))
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
            return None, result

        try:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference start","PASS","")
            resultImg, resultList, status = Input_interface.sync_video_external_inference(videoImgList,extraInfo)
            resultList = convertType(resultList)
            if status == '200':
                pass
            else:
                Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error") 
                result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
                return None, result
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
            try:
                if resultImg == None:
                    resultImg=videoImgList[0]
            except ValueError:
                pass
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            resultList = []
            status = '501'
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,resultList,status,method)
            return None, result

        encodedImg = np.fromstring(resultImg, dtype = np.uint8)
        resultImg = np.array(cv2.imdecode(encodedImg, cv2.IMREAD_UNCHANGED))
        if workflow == "serial":
            Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
        result = Output_interface.common_output(requestDevideId,transactionId,receiveTime,resultList,status,method)
        resultImg = cv2.imencode('.jpg', resultImg)[1]
        try:
            infoThread=Thread(target=Output_interface.send_inferenceInfo,args=(resultImg,result))
            infoThread.daemon=True
            infoThread.start()
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inferenceinfo","PASS",str(result))
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inferenceinfo","FAIL",str(result))
            pass
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inferenceinfo","PASS",str(result))
        return resultImg, result

    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()
        result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"500",method)
        return None, result

def async_inference_func_still(img, requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        workflow,status,statusMsg = Input_interface.service_check(img,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,"still",extraInfo,mimeType)
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","PASS","")
        if status == '200':
            pass
        else:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","FAIL",str(status+" "+statusMsg))
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,status,method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,status,method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,status,method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
                return 100

        try:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference start","PASS","")
            Input_interface.async_still_external_inference(img, requestDevideId,transactionId,receiveTime,method,extraInfo) 

        except Exception as errorMessage:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            Log.make_error_log(errorMessage)
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"501",method)
                return 100

        return 1

    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()
        if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
            if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                return 100

            elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                return 100

            elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                return 100

        else:
            Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"500",method)
            return 100

def async_inference_func_video(imgList,requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        videoImgList = copy.copy(imgList)
        workflow,status,statusMsg = Input_interface.service_check(imgList,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,"video",extraInfo,mimeType)
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","PASS","")
        if status == '200':
            pass
        else:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","FAIL",str(status+" "+statusMsg))
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,status,method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,status,method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,status,method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
                return 100

        try:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference start","PASS","")
            Input_interface.async_video_external_inference(videoImgList, requestDevideId,transactionId,receiveTime,method,extraInfo)

        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"501",method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"501",method)
                return 100

        return 1

    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()
        if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
            if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                return 100

            elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                return 100

            elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,"500",method)
                return 100

        else:
            Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"500",method)
            return 100

def async_external_still_output(resultImg,deviceId,transactionId,receiveTime,result,status,method):
    if Message_IF.serviceConfig['workflow']['type'] == "serial":
        Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
    else:
        if Message_IF.serviceConfig['actionTarget']['type'] == 'REST':
            Output_interface.output_REST_async(resultImg,deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
        elif Message_IF.serviceConfig['actionTarget']['type'] == 'gRPC':
            Output_interface.output_gRPC_async(resultImg,deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
        elif Message_IF.serviceConfig['actionTarget']['type'] == 'FTP':
            Output_interface.output_ftp_async(resultImg,deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
    return 1

def async_external_video_output(resultImg,deviceId,transactionId,receiveTime,result,status,method):
    if Message_IF.serviceConfig['workflow']['type'] == "serial":
        Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
    else:
        if Message_IF.serviceConfig['actionTarget']['type'] == 'REST':
            Output_interface.output_REST_async(resultImg,deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
        elif Message_IF.serviceConfig['actionTarget']['type'] == 'gRPC':
            Output_interface.output_gRPC_async(resultImg,deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
        elif Message_IF.serviceConfig['actionTarget']['type'] == 'FTP':
            Output_interface.output_ftp_async(resultImg,deviceId,transactionId,receiveTime,result,Message_IF.serviceConfig,status,method)
    return 1


def inferenceRun():
    try: 
        Message_IF.serviceToken = Message_IF.get_token(os.environ.get("AiServiceId"))
        Message_IF.serviceConfig = Message_IF.get_configuration(os.environ.get("AiServiceId"))
        Message_IF.seviceDevice = Message_IF.get_devices(os.environ.get("AiServiceId"))
        rabitTh = Thread(target=Message_IF.rabit_conn)
        inputInterfaceBTh = Thread(target=Input_interface.image_input_run)
        rabitTh.start() 
        inputInterfaceBTh.start()
    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()


if __name__ == "__main__":
    inferenceRun()