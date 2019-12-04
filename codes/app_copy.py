import dotenv
from flask import render_template
from flask import request
from flask import Flask
from utils.databases import Features
from utils.essentials import Database

import json
import queue
import threading
# import logging
# import os
# import requests
# import subprocess
# import time

app = Flask(__name__)

dotenv.load_dotenv(dotenv_path='.env')

urls = queue.Queue(maxsize=40) 
ans = {}
cnt = 0

class mythread (threading.Thread):

    def __init__(self,thread_id):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        # self.thread_url = thread_url

    def run(self):
        # print ("Starting thread",self.thread_id)
        while not urls.empty():
            threadLock.acquire()
            self.thread_url=urls.get()
            print (self.thread_id,urls.qsize())
            threadLock.release()
            find_simi(self.thread_id,self.thread_url)
        # print ("Finished thread",self.thread_id)

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
            # print ("aaaaaaaaaaaaaaa")
            pass
        soup = BeautifulSoup(response.text, "html.parser")
        body = soup.findAll('body')
    except:
        print (thread_url)
        pass
    # content = str(body[0])
    # content = content.split('>')
    # print ("Data sample from ",thread_id)

database = Database(Features)
data = database.getdbdata()
data_urls = []
for d in data:
    data_urls.append(d['url'])

@app.route("/sendurl", methods=['POST','GET'])
def start():
    print ("assess credibility")

    # j=0
    # for d in data:
    #     if j == 10:
    #         break
    #     urls.put(d['url'])
    #     j+=1

    # threadLock = threading.Lock()

    # j=0
    # threads = []
    # while not urls.empty() and j<7:
    #     thread1 = mythread(j)
    #     threads.append(thread1)
    #     j+=1
    #     thread1.start()
    # for t in threads:
    #     t.join()

    # print (len(ans))

    # print (request.args['keyword'])

    # data = {"xewd":"dwee"}

    # json_data = json.dumps(data, default=lambda o: '<not serializable>')
    
    # print ("json_data       ",json_data)

    global data_urls
    data = {}
    for url in data_urls:
        data[url] = 0
    json_data = json.dumps(data, default=lambda o: '<not serializable>')

    return json_data


@app.route("/")
def index():
    print ("render source.html")
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def appinfo(url=None):
    pid = os.getpid()
    # print pid
    cmd = ['ps', '-p', str(pid), '-o', "%cpu,%mem,cmd"]
    # print
    while True:
        info = subprocess.check_output(cmd)
        print (info)
        time.sleep(3)

    print ('exiting appinfo')
    return None


if __name__ == "__main__":

    print ("assess")

    app.run(
        threaded=True,
        host='0.0.0.0',
        debug=False,
        port=5050,
    )
