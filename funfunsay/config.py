# -*- coding: utf-8 -*-

APP_NAME = 'funfunsay'
PER_PAGE = 20

class BaseConfig(object):

    DEBUG = False
    TESTING = False

    # mongodb
    FUNFUNSAY_DBNAME = 'ffsdb'

    # os.urandom(24)
    SECRET_KEY = 'secret key'

    # Flask-Babel
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    ACCEPT_LANGUAGES = ['en', 'ch']


class DefaultConfig(BaseConfig):

    DEBUG = True
    SECRET_KEY = 'development key'

    # Flask-Babel
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Shanghai'



class TestConfig(BaseConfig):
    TESTING = True
    CSRF_ENABLED = False
