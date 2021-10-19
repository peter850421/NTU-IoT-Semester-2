import os
import argparse
import cv2
import numpy as np
import base64
import threading
import requests
import json
import time
import utls.config_fuc as conf
import VideoCap
import connetcion
import OpenDoor

def arg_parse():
    parser = argparse.ArgumentParser(description="Main control Thread initialize command")
    parser.add_argument('--config_path', default='./config/global_config.txt', type=str, help='Config file path')
    return parser.parse_args()

class main_thread:  
    def __init__(self,args):
        self.CONFIG_PATH = args.config_path
        self.GLOBAL_CONFIG = conf.read_config(self.CONFIG_PATH)  ##程序全局设置
        self.DEV_VERSION = self.GLOBAL_CONFIG['version']
        self.DEV_CODE = self.GLOBAL_CONFIG['dev_code']
        self.SERVER_URL = self.GLOBAL_CONFIG['server_url']
        self.TIME_OUT = self.GLOBAL_CONFIG['timeout']
        self.FRAME_NUM = int(self.GLOBAL_CONFIG['frame_group_num'])
        self.FRAME_NUM_Veryfy = self.FRAME_NUM*2
        self.URL_RPI_REQ = self.SERVER_URL + 'RPI_control'
        self.URL_RPI_doorbell = self.SERVER_URL + 'RPI_doorbell'
        self.URL_RPI_facereg = self.SERVER_URL + 'face_regnition'  
        self.EVENT_GROUP = {'Global_command':'','Beat_status':'', 'Beat_return':{}} ##用此字典在线程间传值，注意：未测试数据时间线上的同步问题，建议应用于异步指令;
        ##字典的value可以变化为任何数据形态，比如列表和字典；
        #此处使用*_return来处理线程回传数据,使用*_status来监听子线程状态，使用*_command来对子线程发布指令
        self.Beat_thread = connetcion.Beat('Beat_thread',self.GLOBAL_CONFIG, self.EVENT_GROUP)
        self.OpenDoor = OpenDoor.OpenDoor()
        self.OpenDoor.InitializeGPIO()
        self.result = False
        
        #self.caper_module = VideoCap.VideoCap()  ##ADD 0317摄像头模组
        # if self.caper_module.Statue_cap == -1:
        #     print('[Debug] Video initial faild')
        self.awake_flag = False
        self.header = {"Content-Type":"application/json"}

    def update_config(self,update_config_dic):
        self.CONFIG_PATH = args.config_path
        conf.update_config(self.CONFIG_PATH,update_config_dic)

        self.GLOBAL_CONFIG = conf.read_config(self.CONFIG_PATH)  ##程序全局设置
        self.DEV_VERSION = self.GLOBAL_CONFIG['version']
        self.DEV_CODE = self.GLOBAL_CONFIG['dev_code']

        self.SERVER_URL = self.GLOBAL_CONFIG['server_url']
        self.TIME_OUT = self.GLOBAL_CONFIG['timeout']
        self.FRAME_NUM = int(self.GLOBAL_CONFIG['frame_group_num'])
        self.FRAME_NUM_Veryfy = self.FRAME_NUM*2

        self.URL_RPI_REQ = self.SERVER_URL + 'RPI_control'
        self.URL_RPI_doorbell = self.SERVER_URL + 'RPI_doorbell'
        self.URL_RPI_facereg = self.SERVER_URL + 'face_regnition'  
    def run(self): ##运行该线程
        self.Beat_thread.start()  ##心跳线程启动
        while True:
            if self.EVENT_GROUP['Beat_status'] == 'ready':
                self.EVENT_GROUP['Global_command'] = ''
                
            print('[Debug] waiting')
            sig = self.event_from_rpi() ##等待开关信号
            ##检查Beat回传是否需要更新
            if self.EVENT_GROUP['Beat_status'] == 'update':
                Beat_return = self.EVENT_GROUP['Beat_return']
                ##更新设置
                if Beat_return.get('update_config',False):  ##如果有值
                    if Beat_return['update_config'][0] == 'True':
                        update_config = Beat_return['update_config'][1:][0]
                        print('以下设定将被更新：{}'.format(update_config))
                        self.update_config(update_config)  ##需要测试所有线程中传入的Global config字典有没有被更新到

                ##更新程序
                if Beat_return.get('update_program',False):
                    if Beat_return['update_program'][0] == 'True':
                        print('[DEBUG] update program')
                        print(Beat_return['update_program'])
                        update_program = Beat_return['update_program'][1:][0]
                        download_url = update_program['download_url']
                        update_strategy = update_program['update_strategy']
                        update_thread = connetcion.download_update('update',download_url,update_strategy)
                        update_thread.start()
                        ##从指定URL下载更新文件
                self.EVENT_GROUP['Global_command'] = 'update'  
            if sig != 'pass':
                _operator = self.awake(sig)
                _operator() ##根据功能决定是否阻塞
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
    def answer_the_door(self): ##当有人按了门铃后的处理流程
        print('[Debug] answer_the_door')
        self.caper_module = VideoCap.VideoCap()  ##摄像头模组
        if self.caper_module.Statue_cap == -1:
            print('[Debug] Video initial faild')
        img_list = self.caper_module.get_some_frame(frame_num=self.FRAME_NUM) 
        encode_pic_list = [self.cv2_to_base64(np.array(cv2.imencode('.jpg',i)[1]).tostring()) for i in img_list] ##编码图像以便传输
        post_msg = {"image_list":encode_pic_list,"dev_code":self.GLOBAL_CONFIG['dev_code'],"Device-Version":self.GLOBAL_CONFIG['version'],}  ##传输数据格式
        _post = json.dumps(post_msg,sort_keys=True,separators=(',', ':'),ensure_ascii=False) ##打包Json
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


        self.caper_module.release_cam() ##ADD 0317


    def verify_human(self): ##ADD 0316 当有人按了验证按钮后的处理流程
        print('[Debug] verify_human')
        self.caper_module = VideoCap.VideoCap()  ##摄像头模组
        if self.caper_module.Statue_cap == -1:
            print('[Debug] Video initial faild')
        img_list = self.caper_module.get_some_frame(frame_num=self.FRAME_NUM_Veryfy) ##这里可以改为设置文件控制
        encode_pic_list = [self.cv2_to_base64(np.array(cv2.imencode('.jpg',i)[1]).tostring()) for i in img_list] ##编码图像以便传输
        post_msg = {"image_list":encode_pic_list,"dev_code":self.GLOBAL_CONFIG['dev_code'],"Device-Version":self.GLOBAL_CONFIG['version'],}  ##传输数据格式
        _post = json.dumps(post_msg,sort_keys=True,separators=(',', ':'),ensure_ascii=False) ##打包Json
        headers = self.header
        result = False

        try:
            req = requests.post(self.URL_RPI_facereg,json=_post, headers=headers)  ##这里用_post还是post_msg待测试
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
        self.caper_module.release_cam() ##ADD 0317

    def cv2_to_base64(self,byte_img):
        return base64.b64encode(byte_img).decode('utf8')

if __name__ == '__main__':
    args = arg_parse()
    main_control = main_thread(args)
    main_control.run()





