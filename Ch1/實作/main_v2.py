import os
import argparse
import cv2
import numpy as np
import base64
import threading
import requests
import json
import time
import configparser
import VideoCap
import OpenDoor

def arg_parse():
    parser = argparse.ArgumentParser(description="Main control Thread initialize command")
    parser.add_argument('--config_path', default='./config/global_config.txt', type=str, help='Config file path')
    return parser.parse_args()



class main_thread:  
    def __init__(self,args):
        self.CONFIG_PATH = args.config_path
        self.GLOBAL_CONFIG = self.read_config(self.CONFIG_PATH)  ##程序全局設定
        self.DEV_VERSION = self.GLOBAL_CONFIG['version']
        self.DEV_CODE = self.GLOBAL_CONFIG['dev_code']
        self.SERVER_URL = self.GLOBAL_CONFIG['server_url']
        self.TIME_OUT = self.GLOBAL_CONFIG['timeout']
        self.FRAME_NUM = int(self.GLOBAL_CONFIG['frame_group_num'])
        self.FRAME_NUM_Veryfy = self.FRAME_NUM*2
        self.URL_RPI_REQ = self.SERVER_URL + 'RPI_control'
        self.URL_RPI_doorbell = self.SERVER_URL + 'RPI_doorbell'
        self.URL_RPI_facereg = self.SERVER_URL + 'face_regnition'  
        self.EVENT_GROUP = {'Global_command':'','Beat_status':'', 'Beat_return':{}} 
        self.OpenDoor = OpenDoor.OpenDoor()
        self.OpenDoor.InitializeGPIO()
        self.result = False
        
        self.awake_flag = False
        self.header = {"Content-Type":"application/json"}

    def read_config(self,config_path):
        config = configparser.ConfigParser()
        result = config.read(config_path)
        return result['DEFAULT']

    def run(self): ##主程式

        while True:
            if self.EVENT_GROUP['Beat_status'] == 'ready':
                self.EVENT_GROUP['Global_command'] = ''
                
            print('[Debug] waiting')
            sig = self.event_from_rpi() ##等待開關訊號
            ##检查Beat回传是否需要更新
            
            if sig != 'pass':
                _operator = self.awake(sig)
                _operator() ##根據回傳結果執行函式
                self.result = self.OpenDoor.open_door(3, self.result)
            
    
    def event_from_rpi(self):
        event = 'none'
        if self.OpenDoor.get_button_event() == 'door_bell':
            event = 'door_bell'
            self.OpenDoor.reset_button_event()
            
        elif self.OpenDoor.get_button_event() == 'verify_button':
            event = 'verify_button'
            self.OpenDoor.reset_button_event()
        else:
            event = 'pass'
        return event
    def awake(self,command):
        if command == 'door_bell':
            return self.answer_the_door
        elif command == 'verify_button':
            return self.verify_human
        else:
            pass
    def answer_the_door(self): ##當有人按門鈴後的處理流程
        print('[Debug] answer_the_door')
        self.caper_module = VideoCap.VideoCap()  ##攝影機模組
        if self.caper_module.Statue_cap == -1:
            print('[Debug] Video initial faild')
        img_list = self.caper_module.get_some_frame(frame_num=self.FRAME_NUM) 
        encode_pic_list = [self.cv2_to_base64(np.array(cv2.imencode('.jpg',i)[1]).tostring()) for i in img_list] ##對影像進行編碼
        post_msg = {"image_list":encode_pic_list,"dev_code":self.GLOBAL_CONFIG['dev_code'],"Device-Version":self.GLOBAL_CONFIG['version'],}  ##傳送格式
        _post = json.dumps(post_msg,sort_keys=True,separators=(',', ':'),ensure_ascii=False) ##使用Json包裝
        headers = self.header
 
        result = False
        try:
            #print(self.URL_RPI_doorbell)
            req = requests.post(self.URL_RPI_doorbell,json=_post, headers=headers)  ##这里用_post还是post_msg待测试
            time_i = time.time()
            while True:
                time_now = time.time()
                if req.status_code == requests.codes.ok:
                    print('[POST request]check is ok')
                    #print(req.json())
                    break
                if (time_now - time_i) > int(self.TIME_OUT):
                    print('[POST request]time out')
                    break

            result = req.json()['results']  
            self.result = result
        except:
            print('[ERROR] Sending error')


        self.caper_module.release_cam() 


    def verify_human(self): ##當有人按了驗證鈕後的處理流程
        print('[Debug] verify_human')
        self.caper_module = VideoCap.VideoCap()  ##攝影機模組
        if self.caper_module.Statue_cap == -1:
            print('[Debug] Video initial faild')
        img_list = self.caper_module.get_some_frame(frame_num=self.FRAME_NUM_Veryfy) ##設定取得幾個Frame
        encode_pic_list = [self.cv2_to_base64(np.array(cv2.imencode('.jpg',i)[1]).tostring()) for i in img_list] ##對影像進行編碼
        post_msg = {"image_list":encode_pic_list,"dev_code":self.GLOBAL_CONFIG['dev_code'],"Device-Version":self.GLOBAL_CONFIG['version'],}  ##傳送格式
        _post = json.dumps(post_msg,sort_keys=True,separators=(',', ':'),ensure_ascii=False) ##使用Json包裝
        headers = self.header
        result = False

        try:
            req = requests.post(self.URL_RPI_facereg,json=_post, headers=headers) 
            time_i = time.time()
            while True:
                time_now = time.time()
                if req.status_code == requests.codes.ok:
                    print('[POST request]check is ok')
                    #print(req.json())
                    break
                if (time_now - time_i) > int(self.TIME_OUT):
                    print('[POST request]time out')
                    break

            result = req.json()['results']  
            self.result = result
        except:
            print('[ERROR] Sending error')

        print(result)
        if result == True:
            owner_detect = req.json()['owner_detect']
            welconme_word = '\nWelcome home, dear '
            for i in range(len(owner_detect)):
                welconme_word = welconme_word + owner_detect[i]
                if i+1 < len(owner_detect):
                    welconme_word = welconme_word + ', '
                else:
                    welconme_word = welconme_word + '.\n' 
            print("*"*10)
            print(welconme_word)
            print("*"*10)
        self.caper_module.release_cam() 

    def cv2_to_base64(self,byte_img):
        return base64.b64encode(byte_img).decode('utf8')

if __name__ == '__main__':
    args = arg_parse()
    main_control = main_thread(args)
    main_control.run()





