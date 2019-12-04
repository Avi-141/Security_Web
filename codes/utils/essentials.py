import matplotlib  # isort:skip
matplotlib.use('TkAgg')  # isort:skip
import matplotlib.pyplot as pl  # isort:skip

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

import json
import logging
import numpy as np
import os
import pandas as pd
import seaborn as sns
import sys
import threading
import traceback


# with open('data/essentials/weightage.json') as f:
#     weightage_data = json.load(f)

load_dotenv(dotenv_path='.env')

app = Flask(__name__, root_path=os.getcwd())

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
'''
To create our database based off our model, run the following commands
$ python
>>> from app import db
>>> db.create_all()
>>> exit()'''

Base = declarative_base()

# keywords used to check real_world_presence
hyperlinks_attributes = ['contact', 'email', 'help', 'sitemap']

apiList = {
    'lastmod': ['getDate', '', '', 'Integer'],
    'domain': ['getDomain', '', '', 'String(120)'],
    'inlinks': [
        'getInlinks',
        '',
        '',
        'Integer',
    ],
    'outlinks': [
        'getOutlinks',
        '',
        '',
        'Integer',
    ],
    'hyperlinks': [
        'getHyperlinks',
        hyperlinks_attributes,
        '',
        'JSON',
    ],
    'imgratio': ['getImgratio', '', '', 'FLOAT'],
    'brokenlinks': ['getBrokenlinks', '', '', 'Integer'],
    'cookie': ['getCookie', '', '', 'Boolean'],
    'langcount': ['getLangcount', '', '', 'Integer'],
    'misspelled': ['getMisspelled', '', '', 'Integer'],
    # 'wot': ['getWot', '', 'JSON'],
    'responsive': ['getResponsive', '', '', 'Boolean'],
    'ads': ['getAds', '', 'Integer'],
    'pageloadtime': ['getPageloadtime', '', '', 'Integer'],
    'site': [
        '',
        '',
        '',
        'String(120)',
    ],
}


# A class to catch error and exceptions
class WebcredError(Exception):
    """An error happened during assessment of site.
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class MyThread(threading.Thread):
    # def __init__(
    #         self, Module='api', Method=None, Name=None, Url=None, Args=None
    # ):
    #     pass

    def __init__(self, func, Name, Url, Args=None):

        threading.Thread.__init__(self)

        self.func = func
        self.name = Name
        self.url = Url
        self.args = Args
        self.result = None

        if Args and Args != '':
            self.args = Args

    def run(self):
        try:
            if self.args:
                self.result = self.func(self.url, self.args)
            else:
                self.result = self.func(self.url)
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
            try:
                if not ex_value.message == 'Response 202':
                    logger.info('{}:{}'.format(ex_type.__name__, ex_value))
                    logger.info(stack_trace)
            except:
                pass

            self.result = None

    def getResult(self):
        return self.result

    # clear url if Urlattributes object
    def freemem(self):
        self.url.freemem()


class Database(object):
    def __init__(self, database):
        engine = db.engine
        # check existence of table in database
        if not engine.dialect.has_table(engine, database.__tablename__):
            # db.create_all()
            Base.metadata.create_all(engine, checkfirst=True)
            logger.info('Created table {}'.format(database.__tablename__))

        self.db = db
        self.database = database

    def filter(self, name, value):

        # print ("---------------------------------------in filter---------------------------------------")
        # print ("name ",name,"           database ",self.database)
        # print ()
        return self.db.session.query(
            self.database
        ).filter(getattr(self.database, name) == value)

    def exist(self, name, value):

        if self.filter(name, value).count():
            return True

        return False

    def getdb(self):
        return self.db

    def getsession(self):
        return self.db.session

    def add(self, data):
        logger.debug('creating entry')
        reg = self.database(data)
        self.db.session.add(reg)
        self.commit()

    def update(self, name, value, data):
        # TODO pull out only items of available columns of table
        if not self.filter(name, value).count():
            self.add(data)
        else:
            logger.debug('updating entry')
            # we want assess_time only at the time of creation
            if data.get('assess_time'):
                del data['assess_time']

            try:
                self.filter(name, value).update(data)
            # TODO come back and fix the bug
            # ConnectionError can't be adapted by sqlalchemy
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

            self.commit()

    def commit(self):
        try:
            self.db.session.commit()
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
            logger.debug(ex_value)
            logger.debug(stack_trace)

            logger.debug('Rolling back db commit')

            self.getsession().rollback()

    def getdata(self, name=None, value=None):

        # print ("********************************************************************************************")
        a=self.filter(name, value).all()[0].__dict__
        # print (a["url"])
        # print ("********************************************************************************************")
        # return self.filter(name, value).all()[0].__dict__
        return a

    def getcolumns(self):

        return self.database.metadata.tables[self.database.__tablename__
                                             ].columns.keys()

    def gettablename(self):

        return self.database.__tablename__

    def getcolumndata(self, column):
        return self.getsession().query(getattr(self.database, column))

    def getdbdata(self):
        data = []
        for i in self.getcolumndata('url'):
            if not self.getdata('url', i).get('error'):
                data.append(self.getdata('url', i))
        # for d in data:
        #     print (d['url'])
        return data


class Correlation(object):
    def __init__(self):
        pass

    def getcorr(self, data, features_name):

        # supply data to np.coorcoef
        dataframe = pd.DataFrame(
            data=np.asarray(data)[0:, 0:],
            index=np.asarray(data)[0:, 0],
            columns=features_name
        )
        corr = dataframe.corr()

        return corr

    def getheatmap(self, data, features_name):

        corr = self.getcorr(data, features_name)

        # get correlation heatmap
        sns.heatmap(
            corr,
            xticklabels=features_name,
            yticklabels=features_name,
            cmap=sns.diverging_palette(220, 10, as_cmap=True)
        )
        # show graph plot of correlation
        pl.show()
