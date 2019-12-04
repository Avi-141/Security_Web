import dotenv
from flask import render_template
from flask import request
# from flask import jsonify
from utils.databases import Features
# from utils.essentials import app
from utils.essentials import Database
# from utils.essentials import WebcredError
# from utils.webcred import Webcred

import json
import logging
import os
import requests
import subprocess
import time
import threading
import re
import urllib.request
from bs4 import BeautifulSoup
import queue 

urls = queue.Queue(maxsize=40) 
ans = {}
cnt = 0

class mythread (threading.Thread):

    def __init__(self,thread_id):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        # self.thread_url = thread_url

    def run(self):
        print ("Starting thread",self.thread_id)
        while not urls.empty():
            threadLock.acquire()
            self.thread_url=urls.get()
            print (self.thread_id,urls.qsize())
            threadLock.release()
            find_simi(self.thread_id,self.thread_url)
        print ("Finished thread",self.thread_id)

def find_simi(thread_id,thread_url):
    print ("Running thread ",thread_id)
    ans[thread_url] = 1
    try:
        domain = thread_url.split(':')
        domain.pop(0)
        thread_url = "https:"
        for i in domain:
            thread_url += i
        try:
            response = requests.get(thread_url, timeout=3)
        except:
            print ("aaaaaaaaaaaaaaa")
            pass
        soup = BeautifulSoup(response.text, "html.parser")
        body = soup.findAll('body')
    except:
        print (thread_url)
        pass
    # content = str(body[0])
    # content = content.split('>')
    print ("Data sample from ",thread_id)


dotenv.load_dotenv(dotenv_path='.env')
logger = logging.getLogger('WEBCred.app')
logging.basicConfig(
    filename='log/logging.log',
    filemode='a',
    format='[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO
)

if __name__ == "__main__":

    print ("assess")
    database = Database(Features)
    data = database.getdbdata()
    print (len(data))

    j=0
    for d in data:
        if j == 40:
            break
        urls.put(d['url'])
        j+=1

    threadLock = threading.Lock()

    j=0
    threads = []
    while not urls.empty() and j<20:
        thread1 = mythread(j)
        threads.append(thread1)
        j+=1
        thread1.start()
    for t in threads:
        t.join()

    print (len(ans))