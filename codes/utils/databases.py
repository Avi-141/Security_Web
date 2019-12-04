# -*- coding: utf-8 -*-

from utils.essentials import apiList
from utils.essentials import Base
from utils.essentials import db


#  Our database model
class Features(Base):
    __tablename__ = 'features'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(), unique=True)
    redirected = db.Column(db.String())
    genre = db.Column(db.String(120))
    webcred_score = db.Column(db.FLOAT)
    error = db.Column(db.String(120))
    html = db.Column(db.String())
    text = db.Column(db.String())
    assess_time = db.Column(db.Float)

    # create columns of features
    for key in apiList.keys():
        dataType = apiList[key][-1]
        exec (key + " = db.Column(db." + dataType + ")")
        norm = key + 'norm'
        exec (norm + " = db.Column(db.Integer)")

    def __init__(self, data):
        for key in data.keys():
            setattr(self, key, data[key])

    def __repr__(self):
        return self.url


class FeaturesSet(Base):
    __tablename__ = 'feature_set'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(), unique=True)
    error = db.Column(db.String())
    dataset = db.Column(db.String())
    article = db.Column(db.FLOAT())
    shop = db.Column(db.FLOAT())
    help = db.Column(db.FLOAT())
    portrayal_individual = db.Column(db.FLOAT())
    others = db.Column(db.FLOAT())

    def __init__(self, data):
        for key in data.keys():
            setattr(self, key, data[key])

    def __repr__(self):
        return self.url


class Ranks(Base):
    __tablename__ = 'ranks'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(), unique=True)
    redirected = db.Column(db.String())
    error = db.Column(db.String())
    alexa = db.Column(db.Integer())
    wot_confidence = db.Column(db.Integer())
    wot_reputation = db.Column(db.Integer())
    alexa = db.Column(db.Integer())
    wot = db.Column(db.FLOAT())

    def __init__(self, data):
        for key in data.keys():
            setattr(self, key, data[key])

    def __repr__(self):
        return self.url
