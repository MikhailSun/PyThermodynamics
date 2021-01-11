# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 20:55:48 2019

@author: Flanker
"""
import logging
#formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
#
#
#def setup_logger(name, log_file, level=logging.INFO):
#    """Function setup as many loggers as you want"""
#
#    handler = logging.FileHandler(log_file,mode='w')        
#    handler.setFormatter(formatter)
#    
#
#    logger = logging.getLogger(name)
#    logger.setLevel(level)
#    logger.addHandler(handler)
#    
#
#    return logger

def setup_logger(logger_name, log_file, level=logging.INFO, stream=True):
    lgr = logging.getLogger(logger_name)
    lgr.setLevel(level)
    #находим имена хэндлеров, которые уже подключены к логгеру и сохраняем их в список
    
        
        
    
    
    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%H:%M:%S')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    if stream==True: #писать в консоль или нет (но это не точно)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
    name_to_compare=str(fileHandler)
    create_handler=True
    for _handler in lgr.handlers:
        if name_to_compare == str(_handler):
            create_handler=False
    if create_handler==True:
        lgr.addHandler(fileHandler)
        lgr.addHandler(streamHandler)  
    lgr.propagate=False
    



#setup_logger('log1', txtName+"txt")
#setup_logger('log2', txtName+"small.txt")
#logger_1 = logging.getLogger('log1')
#logger_2 = logging.getLogger('log2')
