## v2.1, 11/7/23, re-do v2.0, 
## v2.0, 9/7/23, add pi_command dict and send_pi_command() 
##       DELETE view_light, ADD control for OA, OB, OC
## BoxAPI, v1.00, 5/16/2023, copied from box.py 

import queue
import socket
import time

import select


MSGLEN = 64


class Box:
 ## --- v2.0 start ---
    cmd_code={'LB0':'left_light_off','LB1':'left_light_on','LB2':'left_light_blink', 
         'RB0':'right_light_off','RB1':'right_light_on','RB2':'right_light_blink', 
         'HB0':'house_light_off','HB1':'house_light_on','HB2':'house_light_blink', 
         'VB0':'view_light_off','VB1':'view_light_on','VB2':'view_light_blink', 
         'FB0':'food_light_off','FB1':'food_light_on','FB2':'food_light_blink', 
         'OA0':'out_a_off','OA1':'out_a_on','OA2':'out_a_blink', 
         'OB0':'out_b_off','OB1':'out_b_on','OB2':'out_b_blink', 
         'OC0':'out_c_off','OC1':'out_c_on','OC2':'out_c_blink', 
         'FD0':'NA','FD1':'dispense_pellet','FD2':'dispense_pellet',
         'VC0':'video_camera_off','VC1':'video_camera_on', 'VC2': 'NA',
         'SN0':'session_off','SN1':'session_on','SN2':'NA'}
 ## --- v2.0 end ---   

    
    def __init__(self, box_number, port=3002):
        print('Opening socket...')
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f'Waiting for box {box_number} to connect...')
        self.s.connect((socket.gethostbyname(f'raspberrypi{box_number}'), port))
        print(f'Box {box_number} successfully connected!')

        # to enable sending and receiving at the same time in different threads
        # see https://stackoverflow.com/questions/51104534/python-socket-receive-send-multi-threading
        self.queue = queue.Queue()
        self.rsock, self.ssock = socket.socketpair()
        self.listener_started = False

    def listen_for_events(self, method, timeout_s):
        self.listener_started = True
        self.start = time.time()  #v2.0
        while time.time() - self.start < timeout_s:
            rlist, _, _ = select.select([self.s, self.rsock], [], [], 0)
            for ready_socket in rlist:
                if ready_socket is self.s:
                    message = self.s.recv(MSGLEN)
                    message = message.replace(b' ', b'')
                    if message == b'':
                        print('connection terminated')
                        break
                    elif message:
                        method(*message.decode().split('-'))
                else:
                    self.rsock.recv(1)
                    self.s.send(self.queue.get())
        print('Stop listening')
        self.listener_started = False

    def __del__(self):        
        self.run_cmd('VC0')  # v2.1 was: self.stop_video_capture()
        self.disconnect()
        self.s.close()

    def send(self, msg):
        fillin = MSGLEN - len(msg)
        msg += b' ' * fillin
        if self.listener_started:
            self.queue.put(msg)
            self.ssock.send(b"\x00")
        else:
            self.s.sendall(msg)

    def start_video_capture(self, filename):
        self.send('start_video:{f}'.format(f=filename).encode())

    def disconnect(self):
        self.send(b'terminate')
 
## --- v2.1 run a command sent by Session ---        
    def run_cmd(self,cmd):  ## cmd is a string or bytes type, ex: 'LB2' or b'LB2'
        if isinstance(cmd, bytes): cmd = cmd.decode()  ## if it's in bytes format, need to convert it to string 
        if cmd in self.cmd_code.keys():
            self.send(cmd.encode())
            return True
        else:
            print('[BoxAPI] Command not found: '+ str(cmd))    
            return False
 ## --- v2.1 end ---                    
