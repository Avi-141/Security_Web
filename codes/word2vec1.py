#!/usr/bin/env python
# coding: utf-8

# In[1]:


import gzip
import gensim
import logging
from gensim.test.utils import get_tmpfile
from gensim.models import KeyedVectors
import numpy as np
from scipy import spatial
import re
import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import pronto
from nltk.corpus import wordnet
import queue
import math


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                    level=logging.INFO)


# In[2]:

bfs_queue = queue.Queue(maxsize=1000)
find_words = []


def show_file_contents(input_file):
    with gzip.open(input_file, 'rb') as f:
        for i, line in enumerate(f):
            print(line)
            break


# In[3]:




def read_input(input_file):
    """This method reads the input file which is in gzip format"""

    logging.info("reading file {0}...this may take a while".format(input_file))

    with gzip.open(input_file, 'rb') as f:
        for i, line in enumerate(f):
            if (i % 10000 == 0):
                logging.info("read {0} reviews".format(i))

            # do some pre-processing and return list of words for each review text

            yield gensim.utils.simple_preprocess(line)

# In[7]:


def avg_feature_vector(sentence, model, num_features, index2word_set):
    words = sentence.split()
    feature_vec = np.zeros((num_features, ), dtype='float32')
    n_words = 0
    for word in words:
        if word in index2word_set:
            n_words += 1
            feature_vec = np.add(feature_vec, model[word])
#     print (n_words)
    if (n_words > 0):
        feature_vec = np.divide(feature_vec, n_words)
    return feature_vec

# In[4]:

def own_phrase_simi(list1,list2):
    keys = []
    lines = []
    stop = ["what","why","how","is","am","was","were","that","which","a","an","the"]
    #remove stop words
    for word in list1:
        if not(word in stop):
            keys.append(word)
    for word in list2:
        if not(word in stop):
            lines.append(word)
    sm = 0
    cnt = 0
    while(keys!=[] and lines!=[]):
        w = keys.pop()
        simi = 0
        ind = 0
        for i,word in enumerate(lines):
            try:
                sv = model.wv.similarity(w,word)
            except:
                sv = 0
                pass
            if w == word:
                sv = 1
            if sv > simi:
                simi = sv
                ind = i
        sm += simi
        
        # Weighted similarity
#         if simi > 0.7:
#             w2 = lines.pop(ind)
#             cnt += 1
#         elif simi > 0.4:
#             w2 = lines.pop(ind)
#             cnt += 0.5
#         elif simi >0.05:
#             w2 = lines.pop(ind)
#             cnt += 0.1
#         else:
#             sm -= simi
        w2 = lines.pop(ind)
        cnt += 1
        
#     print (sm)
    if cnt:
        sm /= cnt
#     print (sm)
    return sm





# In[15]:


# DFS

def dfs(node_id):
    
    global find_words
    global model
    global index2word_set
    global ms
    global visited
    global wa,wb
    global mini_simi

    term = ms[node_id]
    visited[term.__hash__()] = 1
    term_name = term.name.lower()
    term_name = ""
    if term_name == "":
        term_repr = term.__repr__()
        for ind,c in enumerate(term_repr):
            if term_repr[ind] == ':':
                break
            if ind-1 and c.isupper() and (term_repr[ind+1].islower() or term_repr[ind+1]==':'):
                term_name += " "
            if c != '<':
                term_name += c
    if term_name == "":
        return
    term_name = term_name.lower()
    
#     global cnt
#     cnt += 1

    w1 = avg_feature_vector(term_name, model=model, num_features=150, index2word_set=index2word_set)
    
    minisimi_local = min(spatial.distance.cosine(w1, wa),spatial.distance.cosine(w1, wb))
    if minisimi_local < mini_simi:
        find_words.append(term_name)
    
    
    children = []
    
    if term.children:
        raw_children = []
        sim_children = []
        for child in term.children:
            if visited[child.__hash__()]:
                continue
            child_name = (child.name).lower()
            child_name = ""
            if child_name == "":
                child_repr = child.__repr__()
                for ind,c in enumerate(child_repr):
                    if child_repr[ind] == ':':
                        break
                    if ind-1 and c.isupper() and (child_repr[ind+1].islower() or child_repr[ind+1]==':'):
                        child_name += " "
                    if c != '<':
                        child_name += c
            if child_name == "":
                continue
            w2 = avg_feature_vector(child_name, model=model, num_features=150, index2word_set=index2word_set)
            neg_sim = spatial.distance.cosine(w1, w2)
            if math.isnan(neg_sim):
                neg_sim = 0
            if neg_sim < mini_simi:
                sim_children.append(neg_sim)
                raw_children.append(child.id)
#             sim_children.append(neg_sim)
#             raw_children.append(child.id)
            
        children = [raw_children for _,raw_children in sorted(zip(sim_children,raw_children))]
        
#     print (term_name)
#     print (children)

    for child_id in children:
        if not visited[ms[child_id].__hash__()]:
            dfs(child_id)


# In[16]:


# BFS


def bfs():

    global find_words
    global model
    global index2word_set
    global ms
    global visited
    global wa,wb
    global mini_simi

    if bfs_queue.empty():
        return
    node_id = bfs_queue.get()
    term = ms[node_id]
    visited[term.__hash__()] = 1
    term_name = term.name.lower()
    term_name = ""
    if term_name == "":
        term_repr = term.__repr__()
        for ind,c in enumerate(term_repr):
            if term_repr[ind] == ':':
                break
            if ind-1 and c.isupper() and (term_repr[ind+1].islower() or term_repr[ind+1]==':'):
                term_name += " "
            if c != '<':
                term_name += c
    if term_name == "":
        return
    term_name = term_name.lower()
#     print (term_name)
       
#     global cnt
#     cnt += 1

    w1 = avg_feature_vector(term_name, model=model, num_features=150, index2word_set=index2word_set)
    
    minisimi_local = min(spatial.distance.cosine(w1, wa),spatial.distance.cosine(w1, wb))
    if minisimi_local < mini_simi:
        find_words.append(term_name)
    
    children = []
    
    if term.children:
        raw_children = []
        sim_children = []
        for child in term.children:
            if visited[child.__hash__()]:
                continue
            child_name = (child.name).lower()
            child_name = ""
            if child_name == "":
                child_repr = child.__repr__()
                for ind,c in enumerate(child_repr):
                    if child_repr[ind] == ':':
                        break
                    if ind-1 and c.isupper() and (child_repr[ind+1].islower() or child_repr[ind+1]==':'):
                        child_name += " "
                    if c != '<':
                        child_name += c
            if child_name == "":
                continue
            w2 = avg_feature_vector(child_name, model=model, num_features=150, index2word_set=index2word_set)
            neg_sim = spatial.distance.cosine(w1, w2)
            if math.isnan(neg_sim):
                neg_sim = 0
            if neg_sim < mini_simi:
                sim_children.append(neg_sim)
                raw_children.append(child.id)
#             sim_children.append(neg_sim)
#             raw_children.append(child.id)
            
        children = [raw_children for _,raw_children in sorted(zip(sim_children,raw_children))]
        
#     print (term_name)
#     print (children)

    for child_id in children:
        if not visited[ms[child_id].__hash__()]:
            bfs_queue.put(child_id)
    bfs()


def initmain():

    global model
    global index2word_set

    input_file = '../dataset.gz'

    # read first line of the dataset
    # show_file_contents(input_file)

    # documents is a list of lists
    documents = list(read_input(input_file))
    logging.info("Done reading dataset")

    # build vocabulary and train model
    model = gensim.models.Word2Vec(
            documents,
            size=150,
            window=10,
            min_count=2,
            workers=10)


# In[5]:


    model.train(documents, total_examples=len(documents), epochs=10)


# In[6]:


    index2word_set = set(model.wv.index2word)

    # own_phrase_simi("abhishek mathur is great".split(),"mathur is awesome".split())


    # s1_afv = avg_feature_vector('firewall', model=model, num_features=150, index2word_set=index2word_set)
    # s2_afv = avg_feature_vector('complex firewall', model=model, num_features=150, index2word_set=index2word_set)

    # sim = 1 - spatial.distance.cosine(s1_afv, s2_afv)
    # print(sim)




    url = 'https://towardsdatascience.com/how-to-web-scrape-with-python-in-4-minutes-bc49186a8460?gi=79ec9ea38660'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    body = soup.findAll('body')
    content = str(body[0])
    without_tags = ""
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
    # words = re.split('=|(|)|-',without_tags)
    words = re.split('\.|,| ',without_tags)

    # content = " "
    # for word in words:
    #     content += word
    # print (without_tags)

    # for word in words:
        # print (word)




    # In[12]:









    # In[13]:

def findrelevantwords(word):

    global find_words
    global model
    global index2word_set
    global ms
    global visited
    global wa,wb
    global mini_simi

    ms = pronto.Ontology("pizza.owl")
    find_words = []
    visited = {}
    cnt = 0
    word = word.lower()
    find_words.append(word)
    list_word = word.split()
    word_with_spaces = list_word[0]
    word = word_with_spaces
    for ind,w in enumerate(list_word):
        if ind > 0:
            word += "_"
            word += w
            word_with_spaces += " "
            word_with_spaces += w
    print (word)
    syn = wordnet.synsets(word)


    # In[14]:


    if syn == []:
        tmp_keyword = word
    else:
        w = syn[0]
        tmp_keyword = w.hypernyms()[0].lemmas()[0].name()
    # print(tmp_keyword)
    keyword = ""
    for ind,c in enumerate(tmp_keyword):
        if c == '_':
            keyword += " "
        else:
            keyword += c
    keyword = keyword.lower()
    find_words.append(keyword)
    print (keyword)
    print (word_with_spaces)
    wa = avg_feature_vector(keyword, model=model, num_features=150, index2word_set=index2word_set)
    wb = avg_feature_vector(word_with_spaces, model=model, num_features=150, index2word_set=index2word_set)
    mini_simi = 0.5




    # In[18]:


    for term in ms:
        visited[term.__hash__()] = 0
        
    children = []
    raw_children = []
    sim_children = []
    w1 = avg_feature_vector(keyword, model=model, num_features=150, index2word_set=index2word_set)
    w11 = avg_feature_vector(word_with_spaces, model=model, num_features=150, index2word_set=index2word_set)
    for child in ms:
    #     print (child)
        if visited[child.__hash__()]:
            continue
        child_name = (child.name).lower()
        child_name = ""
        if child_name == "":
            child_repr = child.__repr__()
            for ind,c in enumerate(child_repr):
                if child_repr[ind] == ':':
                    break
                if ind-1 and c.isupper() and (child_repr[ind+1].islower() or child_repr[ind+1]==':'):
                    child_name += " "
                if c != '<':
                    child_name += c
        if child_name == "":
            continue
        child_name = child_name.lower()
        w2 = avg_feature_vector(child_name, model=model, num_features=150, index2word_set=index2word_set)
        
        neg_sim1 = spatial.distance.cosine(w1, w2)
        if math.isnan(neg_sim1):
            neg_sim1 = 1
        neg_sim11 = spatial.distance.cosine(w11, w2)
        if math.isnan(neg_sim11):
            neg_sim11 = 1
            
    #         print ("...........")
    #     print (child_name,child.id,1-min(neg_sim1,neg_sim11))
        if min(neg_sim1,neg_sim11) < mini_simi:
            sim_children.append(min(neg_sim1,neg_sim11))
            raw_children.append(child.id)
    #     sim_children.append(min(neg_sim1,neg_sim11))
    #     raw_children.append(child.id)
            
    children = [raw_children for _,raw_children in sorted(zip(sim_children,raw_children))]

    find_words = []

    # All terms sorted with decreasing similarity in children[]

    # print (term_name)
    # print (children)

    # DFS

    for child_id in children:
        if not visited[ms[child_id].__hash__()]:
            dfs(child_id)
    # print (cnt)

    print (find_words)
    print ()
    print ()

    for term in ms:
        visited[term.__hash__()] = 0

    find_words_dfs = find_words
    find_words = []


    # BFS

    for child_id in children:
    #     print(ms[child_id].__repr__())
        if not visited[ms[child_id].__hash__()]:
            bfs_queue.put(child_id)
            bfs()
    find_words.insert(0,word_with_spaces)        
    find_words.insert(0,keyword)        
    print (find_words)

    return find_words

# for a,b in enumerate(find_words):
#     try:
#         if b!=find_words_dfs[a]:
#             print (b,find_words_dfs[a])
#     except:
#         pass


# In[19]:








    # Sorted directly w.r.t. similarity

    # w1 = avg_feature_vector(keyword, model=model, num_features=150, index2word_set=index2word_set)
    # w11 = avg_feature_vector(word_with_spaces, model=model, num_features=150, index2word_set=index2word_set)
    # raw_children = []
    # sim_children = []
    # children = []
    # simi_sort = []

    # for term in ms:
    #     term_name = term.name.lower()
    #     term_name = ""
    #     if term_name == "":
    #         term_repr = term.__repr__()
    #         for ind,c in enumerate(term_repr):
    #             if term_repr[ind] == ':':
    #                 break
    #             if ind-1 and c.isupper() and (term_repr[ind+1].islower() or term_repr[ind+1]==':'):
    #                 term_name += " "
    #             if c != '<':
    #                 term_name += c
    #     term_name = term_name.lower()
    #     if term_name == "":
    # #         print (term.__repr__())
    #         continue
    #     w2 = avg_feature_vector(term_name, model=model, num_features=150, index2word_set=index2word_set)
    #     neg_sim1 = spatial.distance.cosine(w1, w2)
    #     if math.isnan(neg_sim1):
    #         neg_sim1 = 1
    #     neg_sim11 = spatial.distance.cosine(w11, w2)
    #     if math.isnan(neg_sim11):
    #         neg_sim11 = 1
    # #     print (word_with_spaces,term_name,term.name,1-min(neg_sim1,neg_sim11))
    # #     if term_name == "firewall a":
    # #         print (term.__repr__(),min(neg_sim1,neg_sim11))
    #     sim_children.append(min(neg_sim1,neg_sim11))
    #     raw_children.append(term_name)
        
    # children = [raw_children for _,raw_children in sorted(zip(sim_children,raw_children))]
    # sim_children.sort()
    # # print (children)
    # for i,child in enumerate(children):
    #     print (child,1-sim_children[i])





