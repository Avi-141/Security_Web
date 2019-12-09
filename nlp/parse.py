import re
import requests
import urllib.request
import time
from bs4 import BeautifulSoup

url = 'https://towardsdatascience.com/how-to-web-scrape-with-python-in-4-minutes-bc49186a8460?gi=79ec9ea38660'
response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

body = soup.findAll('body')
content = str(body[0])

words = re.split('=|<|>|\s|"|\.|-',content)

# print (words)

synonyms = ['snippet of what some of', 'gaseous sample state', 'liquid sample state', 'solid sample state', 'emulsion', 'gaseous sample state', 'liquid sample state', 'solid sample state', 'solution', 'suspension']

count = 0
for ind,word in enumerate(words):
    if word == '':
        continue
    else:
        for keys in synonyms:
            splitkeys = keys.split()
            flag = 1
            for sur,keyw in enumerate(splitkeys):
                try:
                    if keyw != words[ind+sur]:
                        flag = 0
                        break
                except:
                    flag = 0
                    break
            if flag == 1:
                print (keys,ind)
                count += 1
                
print (count)