import dotenv
from flask import render_template
from flask import request
from flask import Flask
from utils.databases import Features
from utils.essentials import Database

import word2vec1
import json
import queue
import threading
import logging
import os
import re
import requests
import urllib.request
from bs4 import BeautifulSoup
import time


app = Flask(__name__)

dotenv.load_dotenv(dotenv_path='.env')

urls = queue.Queue(maxsize=40) 
ans = {}
cnt = 0
rel = []
final_url = []
final_score = []

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
            threadLock.release()
            print (self.thread_id,urls.qsize())
            find_simi(self.thread_id,self.thread_url)
        print ("Finished thread",self.thread_id)


def find_simi(thread_id,thread_url):

# find count of words

    print ("Running thread ",thread_id)
    ans[thread_url] = 1
    try:
        domain = thread_url.split(':')
        domain.pop(0)
        thread_url = "https:"
        for i in domain:
            thread_url += i
        response = requests.get(thread_url,timeout=3)
        soup = BeautifulSoup(response.text, "html.parser")
        body = soup.findAll('body')
        content = str(body[0])
        without_tags = ""
        content_string = ""
        # print (content)
        cnt = 0
        flag = 0
        for c in content:
            if c == '<':
                cnt = 1
            if cnt == 0:
                without_tags += c
                flag = 0
            if c == '>':
                cnt = 0
                if not flag:
                    without_tags += " "
                    flag = 1
        words = re.split('\.|,| ',without_tags)
        for word in words:
            content_string += word
            content_string += " "
        global rel
        fac = 1
        sm1 = 0
        print (content_string)
        j = 0
        for word in rel:
            cnt1 = content_string.count(word)
            print (word,cnt1)
            sm1 += cnt1*fac
            if j > 1:
                fac /= 2
        global final_url
        global final_score
        final_url.append(thread_url)
        final_score.append(sm1)

    except Exception as e:
        # print (e)
        pass
    # content = str(body[0])
    # content = content.split('>')
    # print ("Data sample from ",thread_id)

print ("a")
database = Database(Features)
data = database.getdbdata()
data_urls = []
for d in data:
    data_urls.append(d['url'])
print ("b")

@app.route("/sendurl", methods=['GET'])
def start():
    print ("assess credibility")

    j=0
    global data_urls
    global final_url
    global final_score

    final_url = []
    final_score = []

    for d in data_urls:
        if j == 40:
            break
        urls.put(d)
        j+=1

    keyword=request.args['keyword']
    global rel
    rel = word2vec1.findrelevantwords(keyword)
    print ("rel ",rel)

    j=0
    threads = []
    while not urls.empty() and j<20:
        thread1 = mythread(j)
        threads.append(thread1)
        j+=1
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print ("final score ",final_score)
    print ("final url ",final_url)


    urls1 = [final_url for _,final_url in sorted(zip(final_score,final_url))]
    urls1.reverse()
    final_score.sort(reverse=True)

    print ("final score ",final_score)
    print ("final url ",urls1)

    # print (len(ans))

    # data = {"xewd":"dwee"}

    # json_data = json.dumps(data, default=lambda o: '<not serializable>')
    
    # print ("json_data       ",json_data)

    data = {}
    for i,url in enumerate(urls1):
        data[url] = final_score[i]

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

    word2vec1.initmain()
    print ("assess")
    
    threadLock = threading.Lock()

    app.run(
        threaded=True,
        host='0.0.0.0',
        debug=False,
        port=5050,
    )
