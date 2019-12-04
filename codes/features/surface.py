from ast import literal_eval
from dotenv import load_dotenv
from nltk.corpus import wordnet
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from urllib.parse import urlparse
from utils.essentials import MyThread
from utils.essentials import WebcredError
from utils.urls import Urlattributes

import logging
import os
import re
import requests
import sys
import traceback
import validators

logger = logging.getLogger('WEBCred.surface')
logging.basicConfig(
    filename='log/logging.log',
    filemode='a',
    format='[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    level=logging.INFO
)

load_dotenv()


def funcBrokenllinks(url):
    result = False
    if url:
        try:
            Urlattributes(url)
        except WebcredError:
            result = True
    return result


def funcImgratio(url):
    size = 0
    size = url.getsize()
    return size


# if rank not available, 999999999 wil be returned
def getAlexarank(url):

    if not isinstance(url, Urlattributes):
        url = Urlattributes(url)

    uri = "http://data.alexa.com/data?cli=10&dat=s&url=" + url.geturl()
    uri = Urlattributes(uri)
    soup = uri.getsoup()
    try:
        rank = soup.find("reach")['rank']
    except:
        rank = None
    return rank


def getWot(url):

    if not isinstance(url, Urlattributes):
        url = Urlattributes(url)

    result = (
        "http://api.mywot.com/0.4/public_link_json2?hosts=" + url.geturl() +
        "/&callback=&key=d60fa334759ae377ceb9cd679dfa22aec57ed998"
    )
    uri = Urlattributes(result)
    raw = uri.gettext()
    result = literal_eval(raw[1:-4])
    result = str(result).split(']')[0].split('[')[-1].split(',')
    data = None
    if isinstance(result, list) and len(result) == 2:
        data = {}
        data['reputation'] = int(result[0])
        data['confidence'] = int(result[1])
    return data


def getResponsive(url):

    # should output boolean value
    api_url = 'https://searchconsole.googleapis.com/v1/urlTestingTools/' \
              'mobileFriendlyTest:run'

    response = requests.post(
        api_url,
        json={'url': url.geturl()},
        params={
            'fields': 'mobileFriendliness',
            'key': os.environ['Google_API_KEY']
        }
    )
    if response.status_code / 100 >= 4:
        return None
    response = response.json()

    state = 0

    try:
        if response['mobileFriendliness'] == 'MOBILE_FRIENDLY':
            state = 1
        else:
            pass
            # NOT_MOBILE_FRIENDLY
            # logger.debug(response['mobileFriendliness'])
    except KeyError:
        logger.warning(response['error']['message'])
        state = None

    return state


def getHyperlinks(url, attributes):

    soup = url.getsoup()

    data = {}
    for element in attributes:
        data[element] = 0
        '''
        Using wn.synset('dog.n.1').lemma_names is the correct way to access the
        synonyms of a sense. It's because a word has many senses and it's more
        appropriate to list synonyms of a particular meaning/sense
        '''
        syn = wordnet.synsets(element)
        if syn:
            syn = wordnet.synsets(element)[0].lemma_names()
        lookup = {'header': 0, 'footer': 0}
        percentage = 10

        # looking for element in lookup
        for tags in lookup.keys():
            if soup.find_all(tags, None) and not data[element]:
                lookup[tags] = 1

                text = soup.find_all(tags, None)
                text = text[0].find_all('a', href=True)
                for ss in syn:
                    for index in text:
                        if data[element]:
                            break
                        try:
                            pattern = url.getPatternObj().regexCompile([ss])
                            match, matched = url.getPatternObj().regexMatch(
                                pattern=pattern, data=str(index)
                            )
                        except:
                            logger.debug('Error with patternmatching')
                            return None

                        if match:
                            data[element] = 1
                            break
        '''if lookup tags are not found, then we check in upper and lower
        percentage of text'''
        for tags in lookup.keys():
            if not data[element] and not lookup[tags]:
                text = soup.find_all('a', href=True)
                if tags == 'header':
                    text = text[:(len(text) * (percentage / 100))]

                elif tags == 'footer':
                    text = text[(len(text) * ((100 - percentage) / 100)):]

                for ss in syn:
                    for index in text:
                        if data[element]:
                            break
                        try:
                            pattern = url.getPatternObj().regexCompile([ss])
                            match, matched = url.getPatternObj().regexMatch(
                                pattern=pattern, data=str(index)
                            )
                        except:
                            logger.debug('Error with patternmatching')
                            return None
                        if match:
                            data[element] = 1
                            break

                # such cases where syn is []
                # wordnet has no synonyms for sitemap
                if not data[element]:
                    for index in text:
                        if data[element]:
                            break
                        try:
                            pattern = url.getPatternObj().regexCompile([
                                element
                            ])
                            match, matched = url.getPatternObj().regexMatch(
                                pattern=pattern, data=str(index)
                            )
                        except:
                            logger.debug('Error with patternmatching')
                            return None
                        if match:
                            data[element] = 1
                            break

    return data


def getLangcount(url):
    '''
    idea is to find pattern 'lang' in tags and then iso_lang code in those tags
    there are 2 possible patterns, to match iso_lang -
        ="en"
        =en
    '''

    soup = url.getsoup()

    count = 0
    matched = []
    tags = soup.find_all(href=True)

    for tag in tags:

        tag = str(tag)
        match = re.search("lang", tag, re.I)

        if match:
            pattern = url.patternMatching.getIsoPattern()
            match, pattern = url.getPatternObj().regexMatch(pattern, tag)
            if match:

                # iso_pattern = ="iso"|=iso
                pattern = pattern.split('=')[-1]

                if pattern.startswith('"'):
                    pattern = pattern.split('"')[1]

                if pattern not in matched:
                    matched.append(pattern)
                    count += 1

    # some uni-lang websites didn't mention lang tags
    if count == 0:
        count = 1
    return count


# TODO: think about this
def getImgratio(url):

    total_img_size = 0
    threads = []

    text_size = url.getsize()

    soup = url.getsoup()

    # total_img_size of images
    for link in soup.find_all('img', src=True):
        uri = link.get('src', None)
        if not uri.startswith('http://') and not uri.startswith('https://'):
            uri = url.geturl() + uri

        if validators.url(uri):
            try:
                uri = Urlattributes(uri)
                Method = funcImgratio
                Name = 'Imgratio'
                Url = uri
                func = Method
                t = MyThread(func, Name, Url)
                t.start()
                threads.append(t)
            except Exception:
                # Get current system exception
                ex_type, ex_value, ex_traceback = sys.exc_info()

                # Extract unformatter stack traces as tuples
                trace_back = traceback.extract_tb(ex_traceback)

                # Format stacktrace
                stack_trace = list()

                for trace in trace_back:
                    stack_trace.append(
                        "File : %s , Line : %d, Func.Name : %s, Message : %s" %
                        (trace[0], trace[1], trace[2], trace[3])
                    )

                # print("Exception type : %s " % ex_type.__name__)
                if ex_value.message != 'Response 202':
                    logger.warning(ex_value)
                    logger.debug(stack_trace)

    for t in threads:
        t.join()
        size = t.getResult()
        t.freemem()
        if isinstance(size, int):
            total_img_size += size
        # print total_img_size

    total_size = total_img_size + text_size
    ratio = float(text_size) / total_size

    return ratio


def getAds(url):
    soup = url.getsoup()
    count = 0

    for link in soup.find_all('a', href=True):
        try:
            href = str(link.get('href'))
            if href.startswith('http://') or href.startswith('https://'):

                pattern = url.getPatternObj().getAdsPattern()
                match, pattern = url.getPatternObj().regexMatch(pattern, href)
                if match:
                    count += 1
        except UnicodeEncodeError:
            pass

    return count


def getCookie(url):

    header = url.getheader()
    pattern = url.getPatternObj().regexCompile(['cookie'])

    for key in header.keys():
        match, matched = url.getPatternObj().regexMatch(
            pattern=pattern, data=key
        )

        if match:
            # print key
            return 1

    return 0


def getMisspelled(url):
    text = url.gettext()

    excluded_tags = [
        'NNP', 'NNPS', 'SYM', 'CD', 'IN', 'TO', 'CC', 'LS', 'POS', '(', ')',
        ':', 'EX', 'FW', 'RP'
    ]

    try:
        text = word_tokenize(text)
    except UnicodeDecodeError:
        text = unicode(text, 'utf-8')
        text = word_tokenize(text)

    tags = []
    # print text
    for texts in text:
        i = pos_tag(texts.split())
        i = i[0]
        if i[1] not in excluded_tags and i[0] != i[1]:
            tags.append(i[0])

    # count of undefined words
    count = 0
    for tag in tags:
        try:
            syns = wordnet.synsets(str(tag))
            if syns:
                # [0] is in the closest sense
                syns[0].definition()
        except Exception:
            count += 1

    return count


def getDate(url):
    return url.getlastmod()


def getDomain(url):
    # a fascinating use of .format() syntax
    domain = url.getdomain()
    return domain


def getBrokenlinks(url):
    broken_links = 0
    threads = []
    soup = url.getsoup()

    for link in soup.find_all('a', href=True):
        uri = link.get('href')

        # to include inner links as well
        if not uri.startswith('http://') and not uri.startswith('https://'):
            uri = url.geturl() + uri

        if validators.url(uri):
            Method = funcBrokenllinks
            Name = 'brokenlinks'
            Url = uri
            func = Method
            t = MyThread(func, Name, Url)
            t.start()
            threads.append(t)

    for t in threads:
        t.join()
        if t.getResult():
            broken_links += 1

    logger.debug('broken_links {}'.format(broken_links))
    return broken_links


def getOutlinks(url):
    outlinks = 0

    soup = url.getsoup()
    for link in soup.find_all('a', href=True):
        uri = link.get('href')
        if uri.startswith('https://') or uri.startswith('http://'):

            parsed_uri = urlparse(uri)
            netloc = '{uri.netloc}'.format(uri=parsed_uri)

            if url.getnetloc() != netloc:
                outlinks += 1
                logger.debug('outlinks = {}'.format(outlinks))
    return outlinks


def googleinlink(url):

    API_KEY = os.environ.get('Google_API_KEY')

    inlinks = None
    try:
        # keyword link is used in search query to search only hyperlinks
        uri = (
            'https://www.googleapis.com/customsearch/v1?key=' + API_KEY +
            '&cx=017576662512468239146:omuauf_lfve&q=link:' +
            url.getoriginalurl()
        )
        uri = Urlattributes(uri)
        txt = uri.gettext()

        for line in txt.splitlines():
            if "totalResults" in line:
                break
        inlinks = int(re.sub("[^0-9]", "", line))

    except Exception:
        # Get current system exception
        ex_type, ex_value, ex_traceback = sys.exc_info()

        # Extract unformatter stack traces as tuples
        trace_back = traceback.extract_tb(ex_traceback)

        # Format stacktrace
        stack_trace = list()

        for trace in trace_back:
            stack_trace.append(
                "File : %s , Line : %d, Func.Name : %s, Message : %s" %
                (trace[0], trace[1], trace[2], trace[3])
            )

        # print("Exception type : %s " % ex_type.__name__)
        logger.info('Inlinks error {}'.format(ex_value))
        logger.debug(stack_trace)

    return inlinks


# TODO
def yahooinlink(url):
    pass


# TODO
def binginlink(url):
    pass


# total web-pages which points url
def getInlinks(url):

    inlinks = None
    # request google, yahoo, bing for inlinks
    # take average of there results
    queries = {
        'google': googleinlink,
        # 'yahoo': yahooinlink,
        # 'bing': binginlink,
    }
    threads = []
    for keys in queries.keys():
        Method = queries[keys]
        Name = keys
        func = Method
        Url = url
        thread = MyThread(func, Name, Url)
        thread.start()
        threads.append(thread)
    score = 0
    length = 0
    for t in threads:
        try:
            t.join()
            if t.getResult():
                # HACK to incorporate 0 values
                score = str(int(t.getResult()) + int(score))
                length += 1
        except Exception:
            # Get current system exception
            ex_type, ex_value, ex_traceback = sys.exc_info()

            # Extract unformatter stack traces as tuples
            trace_back = traceback.extract_tb(ex_traceback)

            # Format stacktrace
            stack_trace = list()

            for trace in trace_back:
                stack_trace.append(
                    "File : %s , Line : %d, Func.Name : %s, Message : %s" %
                    (trace[0], trace[1], trace[2], trace[3])
                )

            # print("Exception type : %s " % ex_type.__name__)
            logger.info(ex_value)
            logger.debug(stack_trace)

    if score:
        inlinks = (int(score) / length)
        logger.debug('inlinks {}'.format(inlinks))

    if inlinks == 0:
        # HACK because database and python take 0 as None
        inlinks = -1
    return inlinks


'''install phantomjs and have yslow.js in the path to execute'''


def getPageloadtime(url):

    return url.getloadtime()
    # try:
    #     response = os.popen('phantomjs yslow.js --info basic ' +
    #                         url.geturl()).read()
    #     response = json.loads(response.split('\n')[1])
    #     return (int)(response['lt']) / ((int)(response['r']))
    # except ValueError:
    #     raise WebcredError('FAIL to load')
    # except:
    #     raise WebcredError('Fatal error')


def dimapi(url, api):
    # REVIEW
    try:
        uri = Urlattributes(api)
        raw = uri.gettext()
        # result = literal_eval(raw[1:-2])
        return raw
    except WebcredError:
        raise WebcredError("Give valid API")
    except:
        return 'NA'
