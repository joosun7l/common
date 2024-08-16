from threading import Thread
import Input_interface
import Output_interface
import Message_IF
import gRPC 
import RESTAPI
import os
import cv2
import Log
import copy
import numpy as np

gRPC.templateType = "B"
RESTAPI.templateType ="B"

inference_func_still_inference = None
inference_func_video_inference = None
inference_func_batch_inference = None

def convertType(resultList) :
    if str(type(resultList)) != "<class 'list'>" :
        return [resultList]

    return resultList
    
def async_inference_func_still(img,requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        workflow,status,statusMsg = Input_interface.service_check(img,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,'still',extraInfo,mimeType)
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
            resultImg, resultList = inference_func_still_inference(img,extraInfo)
            resultList = convertType(resultList)
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],'501',method)
                return 100
        try:
            if resultImg is None:
                resultImg=img
            elif str(type(resultImg)) is not  "<class 'numpy.ndarray'>":
                resultImg=np.array(resultImg) 
                resultImg=cv2.cvtColor(resultImg, cv2.COLOR_RGB2BGR)
        except ValueError:
            pass

        if workflow == "serial":
            try:
                Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            except:
                print("serial")
                pass
        else:
            if Message_IF.serviceConfig['actionTarget']['type'] == 'REST':
                Output_interface.output_REST_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            elif Message_IF.serviceConfig['actionTarget']['type'] == 'gRPC':
                Output_interface.output_gRPC_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            elif Message_IF.serviceConfig['actionTarget']['type'] == 'FTP':
                Output_interface.output_ftp_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
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

def async_inference_func_video(imglist, requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        videoImgList = copy.copy(imglist)
        workflow,status,statusMsg = Input_interface.service_check(imglist,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,'video',extraInfo,mimeType)
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
            resultImg, resultList = inference_func_video_inference(videoImgList,extraInfo)
            resultList = convertType(resultList)
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],'501',method)
                return 100

        try:
            if resultImg is None:
                resultImg=imglist[0]
            elif str(type(resultImg)) is not  "<class 'numpy.ndarray'>":
                resultImg=np.array(resultImg) 
                resultImg=cv2.cvtColor(resultImg, cv2.COLOR_RGB2BGR)
        except ValueError:
            pass
        if workflow == "serial":
            try:
                Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            except:
                print("serial")
                pass
        else:
            if Message_IF.serviceConfig['actionTarget']['type'] == 'REST':
                Output_interface.output_REST_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            elif Message_IF.serviceConfig['actionTarget']['type'] == 'gRPC':
                Output_interface.output_gRPC_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            elif Message_IF.serviceConfig['actionTarget']['type'] == 'FTP':
                Output_interface.output_ftp_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
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
            Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],"500",method)
            return 100

def sync_inference_func_still(img, requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        workflow,status,statusMsg = Input_interface.service_check(img,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,'still',extraInfo,mimeType)
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","PASS","") 
        if status == '200':
            pass
        else:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","FAIL",str(status+" "+statusMsg))
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
            return None, result

        try:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference start","PASS","")
            resultImg, resultList = inference_func_still_inference(img,extraInfo)
            resultList = convertType(resultList)
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],'501',method)
            return None, result
        try:
            if resultImg is None:
                resultImg=img
            elif str(type(resultImg)) is not  "<class 'numpy.ndarray'>":
                resultImg=np.array(resultImg) 
                resultImg=cv2.cvtColor(resultImg, cv2.COLOR_RGB2BGR)
        except ValueError:
            pass
        if workflow == "serial":
            try:
                Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            except:
                print("serial")
                pass
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
        return resultImg, result

    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()
        result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"500",method)
        return None, result

def sync_inference_func_video(imglist, requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        videoImgList = copy.copy(imglist)
        workflow,status,statusMsg = Input_interface.service_check(imglist,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,'video',extraInfo,mimeType)
        Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","PASS","") 
        if status == '200':
            pass
        else:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"OpsPreProcessing","FAIL",str(status+" "+statusMsg))
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],status,method)
            return None, result

        try:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference start","PASS","")
            resultImg, resultList = inference_func_video_inference(videoImgList,extraInfo)
            resultList = convertType(resultList)
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            Log.make_trace_error_log()
            result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],'501',method)
            return None, result

        try:
            if resultImg is None:
                resultImg=imglist[0]
            elif str(type(resultImg)) is not  "<class 'numpy.ndarray'>":
                resultImg=np.array(resultImg) 
                resultImg=cv2.cvtColor(resultImg, cv2.COLOR_RGB2BGR)
        except ValueError:
            pass
        if workflow == "serial":
            try:
                Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            except:
                print("serial")
                pass
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
        return resultImg, result

    except Exception as errorMessage:
        Log.make_error_log(errorMessage)
        Log.make_trace_error_log()
        result = Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],"500",method)
        return None, result

def async_inference_func_batch(imglist, requestToken,requestDevideId,transactionId,receiveTime,method,extraInfo,mimeType):
    try:
        videoImgList = copy.copy(imglist)
        workflow,status,statusMsg = Input_interface.service_check(imglist,Message_IF.serviceToken,Message_IF.seviceDevice,Message_IF.serviceConfig,requestToken,requestDevideId,'video',extraInfo,mimeType)
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
            resultImg, resultList = inference_func_batch_inference(videoImgList,extraInfo)
            resultList = convertType(resultList)
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","PASS",str(resultList)) 
        except:
            Log.processing_log(os.environ.get("AiServiceId"),requestDevideId,transactionId,"Inference","FAIL","inference error")
            
            if Message_IF.serviceConfig['workflow']['type'] == "alone" or Message_IF.serviceConfig['workflow']['type'] == "parallel":
                if Message_IF.serviceConfig["actionTarget"]["type"] == "REST":
                    Output_interface.error_output_REST(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "gRPC":
                    Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

                elif Message_IF.serviceConfig["actionTarget"]["type"] == "FTP":
                    Output_interface.error_output_ftp(None,requestDevideId,transactionId,receiveTime,[],Message_IF.serviceConfig,'501',method)
                    return 100

            else:
                Output_interface.error_output_sync(None,requestDevideId,transactionId,receiveTime,[],'501',method)
                return 100

        try:
            if resultImg is None:
                resultImg=imglist[0]
            elif str(type(resultImg)) is not  "<class 'numpy.ndarray'>":
                resultImg=np.array(resultImg) 
                resultImg=cv2.cvtColor(resultImg, cv2.COLOR_RGB2BGR)
        except ValueError:
            pass
        if workflow == "serial":
            try:
                Output_interface.output_gRPC_serial(resultImg,Message_IF.serviceConfig["workflow"]["token"],requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            except:
                print("serial")
                pass
        else:
            if Message_IF.serviceConfig['actionTarget']['type'] == 'REST':
                Output_interface.output_REST_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            elif Message_IF.serviceConfig['actionTarget']['type'] == 'gRPC':
                Output_interface.output_gRPC_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
            elif Message_IF.serviceConfig['actionTarget']['type'] == 'FTP':
                Output_interface.output_ftp_async(resultImg,requestDevideId,transactionId,receiveTime,resultList,Message_IF.serviceConfig,status,method)
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
            Output_interface.error_output_gRPC(None,requestDevideId,transactionId,receiveTime,[],"500",method)
            return 100

def inferenceRun():
    try:
        Message_IF.AiServiceId = os.environ.get("AiServiceId")
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
