import threading
from scipy import spatial
import re
import requests
import urllib.request
import time
from bs4 import BeautifulSoup

class mythread (threading.Thread):

	def __init__(self,thread_id,thread_url):
		threading.Thread.__init__(self)
		self.thread_id = thread_id
		self.thread_url = thread_url

	def run(self):
		print ("Starting thread",self.thread_id)
		find_simi(self.thread_id,self.thread_url)
		print ("Finished thread",self.thread_id)

def find_simi(thread_id,thread_url):
	print ("Running thread ",thread_id)
	response = requests.get(thread_url)
	soup = BeautifulSoup(response.text, "html.parser")
	body = soup.findAll('body')
	content = str(body[0])
	content = content.split('>')
	print ("Data sample from",thread_id,content[1])

urls = []
urls.append("https://radimrehurek.com/gensim/models/keyedvectors.html")
urls.append("https://pypi.org/project/pronto/")
urls.append("https://www.google.com/search?client=ubuntu&channel=fs&q=options+request+instead+of+post+request&ie=utf-8&oe=utf-8")
urls.append("https://github.com/axios/axios/issues/475")
urls.append("https://stackoverflow.com/questions/14908864/how-can-i-use-data-posted-from-ajax-in-flask")
# print (urls)

for i,url in enumerate(urls):
	thread1 = mythread(i,url)
	thread1.start()



