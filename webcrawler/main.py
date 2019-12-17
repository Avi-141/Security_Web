import threading
from queue import Queue
from spider import Spider
from domain import *
from general import *

PROJECT_NAME = 'InfoSec'
HOMEPAGE = 'https://en.wikipedia.org/wiki/Information_security'
#newboston.com for smaller number of urls.
DOMAIN_NAME = get_domain_name(HOMEPAGE)
QUEUE_FILE = PROJECT_NAME + '/queue.txt'
CRAWLED_FILE = PROJECT_NAME + '/crawled.txt'

NUMBER_OF_THREADS = 4

thread_queue = Queue()
Spider(PROJECT_NAME, HOMEPAGE, DOMAIN_NAME)


def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        t = threading.Thread(target=work)
        t.daemon = True
        t.start()

def work():
    while True:
        url = thread_queue.get()
        Spider.crawl_page(threading.current_thread().name, url)
        thread_queue.task_done()

def create_jobs():
    jobs = file_to_set(QUEUE_FILE)
    for link in jobs:
        thread_queue.put(link)
    thread_queue.join()
    crawl()


# Check if there are items in the queue and crawl them

def crawl():
    queued_links = file_to_set(QUEUE_FILE)
    if len(queued_links) > 0:
        print(str(len(queued_links)) + 'links in the queue')
        create_jobs()


create_workers()
crawl()
