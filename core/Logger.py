## v2.0, add file flush

import csv
import time
from datetime import datetime

import pytz
from pythonosc.udp_client import SimpleUDPClient


class Logger:

    def __init__(self, log_path, verbose=True):
        ip = '127.0.0.1'
        port = 2342
        self.bonsai_sender = SimpleUDPClient(ip, port)
        self.f = open(log_path, 'w', newline='')  #v2.0, was f=open()
        self.log_writer = csv.writer(self.f)  #v2.0, was csv.writer(f)
        self.log_writer.writerow(['mouse', 'event', 'pi_timestamp', 'pc_timestamp', 'datetimestamp'])
        self.verbose = verbose

    def log_event(self, mouse, event, pi_timestamp):
        self.log_writer.writerow([mouse, event, pi_timestamp, time.time(), datetime.now()])
        self.f.flush()   # v2.0
        self.bonsai_sender.send_message('/logs',
                                   f'{mouse},{event},{pi_timestamp},{time.time()},{str(datetime.now(pytz.utc))}')

        if self.verbose:
            print(mouse, event)

