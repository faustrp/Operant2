## Sessions - the common module to be loaded by all Schedule modules 

## v1.16, 5/14/2024, send session start code 'S1' to the schedule
## v1.15, 11/17/2023, add logger.log_event(cfg['mouse_name'], val, -1) for log trial #
## v1.14, 8/30/2023, add 'BM' to line 49: if event != 'LL' and event != 'RL' and event != 'BM': return
##                   add print('[Session event]' + event)
## v1.13, 8/29/2023, add inf file 
## V1.00, 5/10/2023, jz
## V1.01, 5/16/2023, change schedule = Schedule(cfg[box_id]) to schedule = Schedule(cfg), cfg is a settings dict
## v1.03, 5/25/23, add box.start=time.time() to reset thr session timer. check 'run' in session_cfg
## v1.04, 5/26/23, change box.py to BoxAPI
## v1.10, 6/1/23, change on_sch_callback() to on_callback():
## v1.11, 6/2/23, fix issues of session_cfg not being global
## v1.12, 6/15/23, rev for c:\Operant file structure


import threading
import time
from pathlib import Path

from Logger import Logger
from BoxAPI import Box

##------ the main function to run a complete session. 'cfg' is a dict with settings such as: 
## {'run':True, 'box_id':5, 'initial':2, 'progressive':0, 'active_lever':'LL', 'time_s': 120, 'log_dir': r'C:\Users\beeler lab\Desktop\DATA\RUDI', 'mouse_name': 'testBox5PR1', 'session':1, 'light_on_lever': False, 'startup_sequence': True},
def Session(cfg,Schedule):        
    box = Box(cfg['box_id'])   
    logger = Logger(Path(cfg['log_dir']) / cfg['mouse_name'])  
    with open(str(Path(cfg['log_dir']) / cfg['mouse_name'] ) + '-' + str(cfg['box_id']) + '.inf', 'w') as f:  ## v1.13
        f.write(str(cfg))    

   
##--- callback handler: this func is activated whenever there is a callback from Schedule or any other module
## 'actions' is a command that is a dict contains device and action, such as {'feeder':'on', 'light':'off'}              
    def on_callback(actions):  ## v1.10
            for key,val in actions.items():
                if key=='feeder':
                    box.dispense_pellet()
                    logger.log_event( cfg['mouse_name'], 'FD', -1)
                elif key=='clight' and val=='blink':
                    box.food_light_blink()
                    logger.log_event(cfg['mouse_name'], 'FB', -1)
                elif key=='llight' and val=='on':
                    box.left_light_on()
                    logger.log_event(cfg['mouse_name'], 'LB1', -1)
                elif key=='llight' and val=='off':
                    box.left_light_off()
                    logger.log_event(cfg['mouse_name'], 'LB0', -1)
                elif key=='rlight' and val=='on':
                    box.right_light_on()
                    logger.log_event(cfg['mouse_name'], 'RB1', -1)
                elif key=='rlight' and val=='off':
                    box.right_light_off()
                    logger.log_event(cfg['mouse_name'], 'RB0', -1)
                else:  ## v1.15
                    logger.log_event(cfg['mouse_name'], val, -1)  
                    
##--- end of callback handler                    
    schedule = Schedule(cfg,on_callback)  ## init a Scheduler object with cfg and callback
   
    lever_press={'LL':False, 'RL': False} # will record initial lever press, only for startup sequence

    ## if startup sequence is not required, the session starts right here
    if not cfg['startup_sequence']:
        box.start_video_capture('{m}_{s}'.format(m= cfg['mouse_name'], s= cfg['session']))
        schedule.on_event('S1') ##1.16 send session start to schedule
        logger.log_event( cfg['mouse_name'], 'video_start', -1)

##--- the event handler, activated everytime the box.listen_for_events detects an event from the Pi
##      'event' is a code, such as LL or RL         
    def on_pi_event(event, pi_timestamp):    
            print('[Session event]' + event)  ## v1.14, for debug 
            if event != 'LL' and event != 'RL' and event != 'BM': return  ## v1.14

            ## ------ wait for left and right lever presses, then start the session.
            if  cfg['startup_sequence']:   # require to press both levers to make sure they work              
                lever_press[event]=True  
                ## if both levers were pressed, start the session
                if lever_press['LL'] and lever_press['RL']:
                    box.start=time.time()  ## v1.02, reset session timer
                    print(f'Box {cfg["box_id"]} started!')       
                    box.start_video_capture('{m}_{s}'.format(m= cfg['mouse_name'], s= cfg['session']))
                    schedule.on_event('S1') ##1.16 send session start to schedule
                    logger.log_event( cfg['mouse_name'], 'video_start', -1)
                    cfg['startup_sequence'] = False
                return
            ## -------- end of startup             

            print( cfg['box_id'],  cfg['mouse_name'], event)
            logger.log_event( cfg['mouse_name'], event, pi_timestamp)

            ## ----- forward the event to Schedule for further processing, v1.10
            schedule.on_event(event) 
            
            ## blink the light if 'light_on_lever' setting is true
            if  cfg['light_on_lever']:
                if event == 'LL':
                    box.left_light_on()
                    time.sleep(0.01)
                    box.left_light_off()
                if event == 'RL':
                    box.right_light_on()
                    time.sleep(0.01)
                    box.right_light_off()
##--- the end of event handler
                    
    ## this function starts to monitor events from the box. and will return after time_s
    box.listen_for_events(on_pi_event,  cfg['time_s']) 
    ## the main functon will stop and exit after box.listen_for_events() returns.
    box.stop_video_capture()
    logger.log_event( cfg['mouse_name'], 'video_stop', -1)
    box.disconnect()
##------- end of the main function for the app


##------- start sessions 
## note: session_cfg is a list of parameters [cfg], it is passed from a Schedule module.  
## cfg is a single item in the list, such as:  {'run':True, 'box_id':5, 'initial':2, 'progressive':0, 'active_lever':'LL', 'time_s': 120, 'log_dir': r'C:\Users\beeler lab\Desktop\DATA\RUDI', 'mouse_name': 'testBox5PR1', 'session':1, 'light_on_lever': False, 'startup_sequence': True},
def run(session_cfg, a_schedule):    
    for cfg in session_cfg:
        if(cfg['run']):
            t = threading.Thread(target=Session, args=[cfg,a_schedule])
            t.start()
 
  
    
