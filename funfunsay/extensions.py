# -*- coding: utf-8 -*-

#db

#flask.ext.mail
#from flask.ext.mail import Mail
#mail = Mail()

from flask.ext.cache import Cache
cache = Cache()


##no need create a global object
##from flask.ext.login import LoginManager
##login_manager = LoginManager()

# build tumblelog system for funfunsay
# jsy, 2012-7-15
from flask.ext.mongoengine import MongoEngine
