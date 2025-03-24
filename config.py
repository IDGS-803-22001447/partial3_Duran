import os 
from sqlalchemy import create_engine
import urllib

class Config(object):
    SECRET_KEY=os.urandom(24)
    SESION_COOKIE_SECURE=False

class DevelopmentConfig(Config):
        DEBUG=True
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:password@127.0.0.1/pizzeria'

        SQLALCHEMY_TRACK_MODIFICATIONS=False
