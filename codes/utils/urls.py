from bs4 import BeautifulSoup
from datetime import datetime
from html2text import html2text
from urllib.parse import urlparse
from utils.databases import Features
from utils.essentials import Database
from utils.essentials import WebcredError

import arrow
import copy
import json
import logging
import re
import requests
import statistics
import sys
import threading
import traceback
import types
import validators

# logger = logging.getLogger('WEBCred.urls')
# logging.basicConfig(
#     filename='log/logging.log',
#     filemode='a',
#     format='[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s',
#     datefmt='%m/%d/%Y %I:%M:%S %p',
#     level=logging.DEBUG
# )

global patternMatching
patternMatching = None

# represents the normalized class of each dimension
"""
normalizedData[dimension_name].getscore(dimension_value)
gives normalized_value
"""
global normalizedData
normalizedData = None

global lastmodMaxMonths
# 3 months
lastmodMaxMonths = 93

# define rules to normalize data
global normalizeCategory
normalizeCategory = {
    '3': {
        'outlinks': 'reverse',
        'inlinks': 'linear',
        'ads': 'reverse',
        'brokenlinks': 'reverse',
        # TODO relook at it's normalization
        'pageloadtime': 'reverse',
        'imgratio': 'linear'
    },
    '2': {
        'misspelled': {
            0: 1,
            'else': 0
        },
        'responsive': {
            'true': 1,
            'false': 0,
            '0': 0,
            '1': 1,
        },
        'langcount': {
            1: 0,
            'else': 1
        },
        'domain': {
            'gov': 1,
            'org': 0,
            'edu': 1,
            'com': 0,
            'net': 0,
            'else': -1
        },
        "lastmod": {
            lastmodMaxMonths: 1,
            'else': 0,
        },
    },
    'misc': {
        'hyperlinks': "linear"
    },
}


# A class for pattern matching using re lib
class PatternMatching(object):
    def __init__(self, lang_iso=None, ads_list=None):
        if lang_iso:
            try:
                iso = open(lang_iso, "r")
                self.isoList = iso.read().split()
                isoList = []
                for code in self.isoList:
                    # isoList.pop(iso)
                    isoList.append(str('=' + code))
                    isoList.append(str('="' + code + '"'))
                self.isoList = isoList
                self.isoPattern = self.regexCompile(self.isoList)
                iso.close()
            except WebcredError as e:
                raise WebcredError(e.message)
            except:
                raise WebcredError('Unable to open {} file'.format(lang_iso))
        else:
            logger.debug('Provide Language iso file')

        if ads_list:
            try:
                ads = open(ads_list, "r")
                self.adsList = ads.read().split()
                self.adsPattern = self.regexCompile(self.adsList)
                ads.close()
                print ('successfull with ads compilation')
            except WebcredError as e:
                raise WebcredError(e.message)
            except:
                raise WebcredError('Unable to open {} file'.format(ads_list))
        else:
            logger.debug('Provide a good ads list')

    def getIsoList(self):
        return self.isoList

    def getAdsList(self):
        return self.adsList

    def getAdsPattern(self):
        return self.adsPattern

    def getIsoPattern(self):
        return self.isoPattern

    def regexCompile(self, data=None):
        if not data:
            raise WebcredError('Provide data to compile')

        pattern = []
        for element in data:
            temp = re.compile(re.escape(element), re.X)
            pattern.append(temp)
        return pattern

    def regexMatch(self, pattern=None, data=None):

        if not pattern:
            raise WebcredError('Provide regex pattern')

        if not data:
            raise WebcredError('Provide data to match with pattern')

        for element in pattern:
            match = element.search(data)
            if match:
                break

        if match:
            return True, element.pattern
        else:
            return False, None


# A class to get normalized score for given value based on collectData
class Normalize(object):

    # data = json_List
    # name =parameter to score
    def __init__(self, data=None, name=None):
        if not data or not name:
            raise WebcredError('Need 3 args, 2 pass')

        self.reverse = self.dataList = self.mean = self.deviation = None
        self.factorise = None

        self.data = data
        self.name = name[0]

        if isinstance(name[1], str):
            if name[1] == 'reverse':
                self.reverse = True

        elif isinstance(name[1], dict):
            self.factorise = name[1]

    def getdatalist(self):
        if not self.dataList:
            dataList = []
            NumberTypes = (
            # types.IntType, types.LongType, types.FloatType, types.ComplexType         #python 2
            int, float, complex                                                         #python 3
            )
            for element in self.data:
                if element.get(self.name) and isinstance(element[self.name],
                                                         NumberTypes):
                    # # done for decimal values like 0.23
                    # if isinstance(element[self.name], float):
                    #     element[self.name] = int(element[self.name]*1000000)
                    dataList.append(element[self.name])
            self.dataList = dataList

        # print self.dataList
        return self.dataList

    def normalize(self):
        NumberTypes = (
            # types.IntType, types.LongType, types.FloatType, types.ComplexType         #python 2
            int, float, complex                                                         #python 3
        )
        for index in range(len(self.data)):
            if isinstance(self.data[index].get(self.name), NumberTypes):
                self.data[index][self.name] = self.getscore(
                    self.data[index][self.name]
                )

        return self.data

    def getnormalizedScore(self, value):
        NumberTypes = (
            # types.IntType, types.LongType, types.FloatType, types.ComplexType         #python 2
            int, float, complex                                                         #python 3
        )
        if isinstance(value, NumberTypes):
            return self.getscore(value)

        # case when dimension value throws error
        # 0 because it  neither add nor reduces credibility
        return 0

    def getdata(self):
        return self.data

    def getmean(self):
        if not self.mean:
            self.mean = statistics.mean(self.getdatalist())
            print ("mean=", self.mean, self.name)
        return self.mean

    def getdeviation(self):
        if not self.deviation:
            self.deviation = statistics.pstdev(self.getdatalist())
            print ("deviation=", self.deviation, self.name)
        return self.deviation

    def getscore(self, value):
        mean = self.getmean()
        deviation = self.getdeviation()
        """
        sometimes mean<deviation and surpass good results,
        as no value is less than 0
        """
        netmd = mean - deviation
        if netmd < 0:
            netmd = 0

        if value <= (netmd):
            if self.reverse:
                return 1
            return -1

        else:
            if value >= (mean + deviation):
                if self.reverse:
                    return -1
                return 1
            return 0

    def getfactoise(self, value):
        global lastmodMaxMonths

        # condition for lastmod
        if self.name == "lastmod":
            value = self.getDateDifference(value)
            if value < lastmodMaxMonths:
                return self.factorise.get(lastmodMaxMonths)

        # condition for everthing else
        else:
            for k, v in self.factorise.items():
                if str(value) == str(k):
                    return v
        if 'else' in self.factorise.keys():
            return self.factorise.get('else')

    # return dayDiffernce form now and value
    def getDateDifference(self, value):
        try:
            # strptime  = string parse time
            # strftime = string format time
            try:
                lastmod = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S').date()
            except:
                lastmod = arrow.get(value).datetime.date()
            dayDiffernce = (datetime.now().date() - lastmod).days
            return dayDiffernce
        except:
            # in case of ValueError, lastmod will sum to WEBcred Score
            return 100000

    def factoise(self):
        if not self.factorise:
            raise WebcredError('Provide attr to factorise')
        global lastmodMaxMonths

        for index in range(len(self.data)):
            if self.data[index].get(self.name):
                modified = 0

                # condition for lastmod
                if self.name == "lastmod":
                    value = self.data[index][self.name]
                    value = self.getDateDifference(value)
                    if value < lastmodMaxMonths:
                        self.data[index][
                            self.name
                        ] = self.factorise.get(lastmodMaxMonths)
                        modified = 1

                # condition for everything else
                else:
                    value = self.data[index][self.name]
                    for k, v in self.factorise.items():
                        if str(value) == str(k):
                            self.data[index][self.name] = v
                            modified = 1
                if not modified:
                    if 'else' in self.factorise.keys():
                        self.data[index][self.name
                                         ] = self.factorise.get('else')
        return self.data


# A class to use extract url attributes
class Urlattributes(object):
    # HACK come back and do this properly
    try:
        # TODO fetch ads list dynamically from org
        if not patternMatching:
            patternMatching = PatternMatching(
                lang_iso='data/essentials/lang_iso.txt',
                ads_list='data/essentials/easylist.txt'
            )
            print ('end patternMatching')

        global normalizedData
        global normalizeCategory
        if not normalizedData:
            normalizedData = {}
            # read existing data
            old_data = 'data/json/data2.json'
            old_data = open(old_data, 'r').read()
            old_data = old_data.split('\n')
            new_data = 'data/json/new_data.json'
            new_data = open(new_data, 'r').read()
            new_data = new_data.split('\n')
            re_data = 'data/json/re_data.json'
            re_data = open(re_data, 'r').read()
            re_data = re_data.split('\n')

            # list with string/buffer as values
            file_ = list(set(new_data + old_data + re_data))

            # final json_List of data
            data = []
            for element in file_[:-1]:
                try:
                    metadata = json.loads(str(element))
                    # if metadata.get('redirected'):
                    #     url = metadata['redirected']
                    # else:
                    #     url = metadata['Url']
                    # obj = utils.Domain(url)
                    # url = obj.getnetloc()
                    # metadata['domain_similarity'] = scorefile_data.get(url)
                except:
                    continue
                if metadata.get('Error'):
                    continue
                data.append(metadata)

            # get data from postgres
            db = Database(Features)
            data = db.getdbdata()

            it = normalizeCategory['3'].items()
            for k in it:
                normalizedData[k[0]] = Normalize(data, k)
                data = normalizedData[k[0]].normalize()

            it = normalizeCategory['misc'].items()
            for k in it:
                tmp_it = k[0]
            it = tmp_it
            # summation of hyperlinks_attribute values
            for index in range(len(data)):
                if data[index].get(it[0]):
                    sum_hyperlinks_attributes = 0
                    tempData = data[index].get(it[0])
                    try:
                        for k, v in tempData.items():
                            sum_hyperlinks_attributes += v
                    except:
                        # TimeOut error clause
                        pass
                    finally:
                        data[index][it[0]] = sum_hyperlinks_attributes

            normalizedData[it[0]] = Normalize(data, it)
            data = normalizedData[it[0]].normalize()

            for k in normalizeCategory['2'].items():
                print ("normalizing", k)
                normalizedData[k[0]] = Normalize(data, k)
                data = normalizedData[k[0]].factoise()

            # csv_filename = 'analysis/WebcredNormalized.csv'
            #
            # pipe = Pipeline()
            # csv = pipe.convertjson(data)
            # f = open(csv_filename,'w')
            # f.write(csv)
            # f.close()

    except WebcredError as e:
        # raise WebcredError(e.message)
        pass

    def __init__(self, url=None):
        # print 'here'
        if patternMatching:
            self.patternMatching = patternMatching

        self.hdr = {'User-Agent': 'Mozilla/5.0'}
        self.requests = self.urllibreq = self.soup = self.text = None
        self.netloc = self.header = self.lastmod = self.size = \
            self.html = self.domain = self.loadTime = None
        self.lock = threading.Lock()
        if url:
            if not validators.url(url):
                raise WebcredError('Provide a valid url')
            self.url = url
            self.originalUrl = copy.deepcopy(url)

            # case of redirections
            resp = self.getrequests()
            if resp.status_code / 100 >= 4:
                raise WebcredError('Response 202')
            self.url = resp.url

        else:
            raise WebcredError('Provide a url')

    def getloadtime(self):
        return self.loadTime

    def getoriginalurl(self):
        return self.originalUrl

    def getjson(self):
        return self.getrequests().json()

    def geturl(self):
        return self.url

    def gethdr(self):
        return self.hdr

    def getheader(self):
        if not self.header:
            self.header = self.geturllibreq().headers

        return self.header

    def getrequests(self):
        if not self.requests:
            self.requests = self.geturllibreq()

        return self.requests

    def geturllibreq(self):
        # with self.lock:
        if not self.urllibreq:
            try:
                now = datetime.now()
                self.urllibreq = requests.get(url=self.url, headers=self.hdr)
                self.loadTime = int((datetime.now() - now).total_seconds())
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
                raise WebcredError(ex_value)
                # logger.info(stack_trace)
                # HACK if it's not webcred error,
                #  then probably it's python error

        # print self.urllibreq.geturl()
        return self.urllibreq

    def clean_html(self, html):
        """
        Copied from NLTK package.
        Remove HTML markup from the given string.

        :param html: the HTML string to be cleaned
        :type html: str
        :rtype: str
        """

        # First we remove inline JavaScript/CSS:
        cleaned = re.sub(
            r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip()
        )
        # Then we remove html comments.
        # This has to be done before removing regular
        # tags since comments can contain '>' characters.
        cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
        # Next we can remove the remaining tags:
        cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
        # Finally, we deal with whitespace
        cleaned = re.sub(r"&nbsp;", " ", cleaned)
        cleaned = re.sub(r"  ", " ", cleaned)
        cleaned = re.sub(r"  ", " ", cleaned)
        return cleaned.strip()

    def gettext(self):
        if not self.text:
            text = self.gethtml()
            text = self.clean_html(text)
            self.text = html2text(text)

        return self.text

    def gethtml(self):
        if not self.html:
            self.html = self.getrequests().text
        return self.html

    def getsoup(self, parser='html.parser'):
        data = self.getrequests().text
        try:
            self.soup = BeautifulSoup(data, parser)
        except:
            raise WebcredError('Error while parsing using bs4')

        return self.soup

    def getnetloc(self):
        if not self.netloc:
            try:
                parsed_uri = urlparse(self.geturl())
                self.netloc = '{uri.netloc}'.format(uri=parsed_uri)
            except:
                logger.debug('Error while fetching attributes from parsed_uri')

        return self.netloc

    def getdomain(self):
        if not self.domain:
            try:
                netloc = self.getnetloc()
                self.domain = netloc.split('.')[-1]
            except:
                raise WebcredError('provided {} not valid'.format(netloc))

        return self.domain

    def getPatternObj(self):
        try:
            return self.patternMatching
        except:
            raise WebcredError('Pattern Obj is NA')

        # self.isoList =

    def getsize(self):
        if not self.size:
            t = self.gettext()
            try:
                self.size = len(t)
            except:
                raise WebcredError('error in retrieving length')
        return self.size

    def getlastmod(self):

        if self.lastmod:
            return self.lastmod

        try:
            data = None
            # fetching data form archive
            for i in range(15):
                uri = "http://archive.org/wayback/available?url=" + \
                      self.geturl()
                uri = Urlattributes(uri)
                resp = uri.geturllibreq()
                if resp.status_code / 100 < 4:
                    resp = resp.json()
                    try:
                        data = arrow.get(
                            resp['archived_snapshots']['closest']['timestamp'],
                            'YYYYMMDDHHmmss'
                        ).timestamp
                    except:
                        data = str(0)
                if data:
                    self.lastmod = int(data)
                    break
        #     if not data:
        #         resp = self.geturllibreq()
        #         lastmod = str(resp.headers.getdate('Date'))
        #             'Mon, 09 Jul 2018 07:29:16 GMT'
        #              Error z directive is bad format
        #         lastmod = datetime.strptime(
        #             str(lastmod), '(%a, %d %b %Y %H:%M:%S %z)'
        #         )
        #         lastmod = datetime.strptime(
        #             we.headers.get('Date'), '(%a, %d %b %Y %H:%M:%S %z)'
        #         )
        #             str(lastmod), '(%Y, %m, %d, %H, %M, %S, %f, %W, %U)'
        #         )
        #         self.lastmod = lastmod.isoformat()
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
            self.lastmod = None

        return self.lastmod

    def freemem(self):
        del self
