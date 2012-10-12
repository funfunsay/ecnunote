# -*- coding: utf-8 -*-

#db

#flask.ext.mail
#from flask.ext.mail import Mail
#mail = Mail()

from flask.ext.cache import Cache
cache = Cache()

from flask.ext.pymongo import PyMongo
mongo = PyMongo()

##no need create a global object
##from flask.ext.login import LoginManager
##login_manager = LoginManager()
