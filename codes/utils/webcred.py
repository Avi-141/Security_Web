from datetime import datetime
from features import surface
from utils.essentials import apiList
from utils.essentials import MyThread
from utils.essentials import WebcredError
from utils.urls import normalizeCategory
from utils.urls import normalizedData
from utils.urls import Urlattributes

import logging
import os
import re
import sys
import traceback

# logger = logging.getLogger('WEBCred.webcred')
# logging.basicConfig(
#     filename='log/logging.log',
#     filemode='a',
#     format='[%(asctime)s] {%(name)s:%(lineno)d} %(levelname)s - %(message)s',
#     datefmt='%m/%d/%Y %I:%M:%S %p',
#     level=logging.INFO
# )

# map feature to function name
# these keys() are also used to define db columns


class Webcred(object):
    def __init__(self, db, request):
        self.db = db
        self.request = request

    def assess(self):

        now = datetime.now()

        if not isinstance(self.request, dict):
            self.request = dict(self.request.args)

        data = {}
        req = {}
        req['args'] = {}
        percentage = {}
        site = None
        dump = True
        try:
            # get percentage of each feature
            # and copy self.request to req['args']
            # TODO come back and do this properly
            for keys in apiList.keys():
                if self.request.get(keys, None):
                    # because self.request.args is of ImmutableMultiDict form
                    if isinstance(self.request.get(keys, None), list):
                        req['args'][keys] = str(self.request.get(keys)[0])
                        perc = keys + "Perc"
                        if self.request.get(perc):
                            percentage[keys] = self.request.get(perc)[0]
                    else:
                        req['args'][keys] = self.request.get(keys)
                        perc = keys + "Perc"
                        if self.request.get(perc):
                            percentage[keys] = self.request.get(perc)

            # to show wot ranking
            # req['args']['wot'] = "true"
            data['url'] = req['args']['site']

            site = Urlattributes(url=req['args'].get('site', None))

            # get genre
            # WARNING there can be some issue with it
            data['genre'] = self.request.get('genre', None)

            if data['url'] != site.geturl():
                data['redirected'] = site.geturl()

            data['lastmod'] = site.getlastmod()

            # site is not a WEBCred parameter
            del req['args']['site']

            # check database,
            # if url is already present?
            if self.db.filter('url', data['url']).count():
                '''
                if lastmod not changed
                    update only the columns with None value
                else update every column
                '''
                if self.db.filter(
                        'lastmod',
                        data['lastmod']).count() or not data['lastmod']:
                    # get all existing data in dict format
                    data = self.db.getdata('url', data['url'])

                    # check the ones from columns which have non None value
                    '''
                    None value indicates that feature has not
                    successfully extracted yet
                    '''
                    for k, v in data.items():
                        if v or str(v) == '0':
                            # always assess loadtime
                            if k != 'pageloadtime':
                                req['args'][k] = 'false'
                    dump = False
                else:
                    data = self.db.getdata('url', data['url'])

            data = self.extractValue(req, apiList, data, site)


            # HACK 13 is calculated number, refer to index.html, where new
            # dimensions are dynamically added
            # create percentage dictionary
            number = 13
            # TODO come back and do this properly

            print ()
            print ()
            print ()
            print("no error 1")
            print ()
            print ()
            print ()

            while True:
                dim = "dimension" + str(number)
                API = "api" + str(number)
                if dim in self.request.keys():
                    try:
                        data[self.request.get(dim)[0]] = surface.dimapi(
                            site.geturl(),
                            self.request.get(API)[0]
                        )
                        perc = API + "Perc"
                        percentage[dim] = self.request.get(perc)[0]
                    except WebcredError as e:
                        data[self.request.get(dim)[0]] = e.message
                    except:
                        data[self.request.get(dim)[0]] = "Fatal ERROR"
                else:
                    break
                number += 1

            print ()
            print ()
            print ()
            print("no error 2")
            print ()
            print ()
            print ()

            data = webcredScore(data, percentage)

            data['error'] = None
            print ("data1error                                    ",data['error'])

        except WebcredError as e:
            data['error'] = e.message
            print ('python error')
            print()
            dump = False
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
            # HACK if it's not webcred error,
            #  then probably it's python error
            data['error'] = 'Fatal Error'
            dump = False
            logger.debug(data['url'])
        finally:

            now = str((datetime.now() - now).total_seconds())
            data['assess_time'] = now

            # store it in data
            self.db.update('url', data['url'], data)

            # dump text and html of html
            if dump:
                self.dumpRaw(site)

            data = self.db.getdata('url', data['url'])

            # prevent users to know of dump location
            del data['html']
            del data['text']

            logger.debug(data['url'])

            logger.debug('Time = {}'.format(now))


            print ("data2error                                    ",data['error'])


            return data

    # dump text and html of html
    def dumpRaw(self, site):
        if not site:
            return

        # location where this data will be dumped
        loct = 'data/dump/'

        dump = {
            'html': {
                'function': 'gethtml'
            },
            'text': {
                'function': 'gettext'
            },
        }
        data = {}
        filename = re.sub('^http*://', '', site.getoriginalurl())
        for i in dump.keys():
            location = (os.sep).join([
                loct, i,
                (os.sep).join(filename.split('/')[:-1])
            ])
            if not os.path.exists(location):
                os.makedirs(location)
            location = (os.sep).join([location, filename.split('/')[-1]])
            fi = open(location, 'w')
            func = getattr(site, dump[i]['function'])
            data[i] = location
            raw = func()
            try:
                fi.write(raw)
            except UnicodeEncodeError:
                fi.write(raw.encode('utf-8'))
            fi.close()

        # update db with locations of their dump
        self.db.update('url', site.getoriginalurl(), data)

    # to differentiate it with DB null value
    def extractValue(self, req, apiList, data, site):
        # assess requested features
        threads = []
        for keys in req['args'].keys():
            if str(req['args'].get(keys, None)) == "true":
                Method = apiList[keys][0]
                Name = keys
                Url = site
                Args = apiList[keys][1]
                func = getattr(surface, Method)
                thread = MyThread(func, Name, Url, Args)
                thread.start()
                threads.append(thread)

        # wait to join all threads in order to get all results
        maxTime = 300
        for t in threads:
            t.join(maxTime)
            data[t.getName()] = t.getResult()
            logger.debug('{} = {}'.format(t.getName(), data[t.getName()]))

        return data


# esp. are we removing any outliers?
def webcredScore(data, percentage):
    # percentage is dict
    # score varies from -1 to 1
    score = 0
    # take all keys of data into account

    for k, v in data.items():

        try:
            if k in normalizeCategory['3'].keys() and k in percentage.keys():
                name = k + "norm"
                data[name] = normalizedData[k].getnormalizedScore(v)
                score += data[name] * float(percentage[k])

            if k in normalizeCategory['2'].keys() and k in percentage.keys():
                name = k + "norm"
                data[name] = normalizedData[k].getfactoise(v)
                score += data[name] * float(percentage[k])

            if k in normalizeCategory['misc'
                                      ].keys() and k in percentage.keys():
                sum_hyperlinks_attributes = 0
                try:
                    for key, value in v.items():
                        sum_hyperlinks_attributes += value
                    name = k + "norm"
                    data[name] = normalizedData[k].getnormalizedScore(
                        sum_hyperlinks_attributes
                    )
                    score += data[name] * float(percentage[k])
                except:
                    logger.info('Issue with misc normalizing categories')
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

    print (score)

    data["webcred_score"] = score / 100

    # TODO add Weightage score for new dimensions
    return data
