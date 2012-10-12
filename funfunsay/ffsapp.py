# -*- coding: utf-8 -*-
"""
this is the main app entry.
todo: Remove all sub-apps.
"""
from __future__ import with_statement

#import pygame
import os
import sys
from datetime import datetime

from hashlib import md5
from flask import (Flask, request, render_template, g, session, url_for)
from flask.ext.babel import Babel
from funfunsay.config import DefaultConfig, APP_NAME
from funfunsay.views import homesite, funnote
from funfunsay.extensions import cache, fun2say, vpymongo
from flask.ext.login import login_user, current_user, logout_user
from funfunsay import utils
from funfunsay.models import User
from flask.ext.fun2say import Fun2say
from funfunsay.utils import html2text
from flask.ext.babel import gettext as _
from funfunsay.utils import randbytes
from flask.ext.login import session_protected


# For import *
__all__ = ['create_app']

DEFAULT_BLUEPRINTS = (
    homesite,
    funnote,
)

MAX_LEN_P = 100 #max text length for a principle

def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)

def make_note_brief(source):
    if len(source)<=50:
        return source

    return source[:50] + "..."


def create_app(config=None, app_name=None, blueprints=None):
    """Create a Flask app."""
    if app_name is None:
        app_name = APP_NAME
    if blueprints is None:
        blueprints = DEFAULT_BLUEPRINTS

    app = Flask(app_name)

    configure_app(app, config)
    configure_blueprints(app, blueprints)
    configure_extensions(app)
    #configure_logging(app)
    configure_template_filters(app)
    #configure_error_handlers(app)
    #must configure hook after extensions is configured!
    configure_hook(app)


    # add some filters to jinja
    app.jinja_env.filters['datetimeformat'] = utils.format_datetime
    app.jinja_env.globals['format_datetime_now'] = utils.format_datetime_now
    app.jinja_env.filters['gravatar'] = utils.gravatar_url
    app.jinja_env.filters['user'] = User.get_user_profile
    app.jinja_env.filters['myvote'] = User.my_vote
    app.jinja_env.filters['scoreformat'] = int
    app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    app.jinja_env.globals['make_note_brief'] = make_note_brief
    app.jinja_env.globals['html2text'] = html2text.html2text

    #print "app created"
    return app



def configure_app(app, config):
    """Configure app from object, parameter and env."""
    app.config.from_object(DefaultConfig)
    if config is not None:
        app.config.from_object(config)
    # Override setting by env var without touching codes.
    app.config.from_envvar('FUNFUNSAY_CONFIG', silent=True)


def configure_extensions(app):
    #from simplekv.memory import DictStore
    #from flask.ext.kvsession import KVSessionExtension
    #store = DictStore()
    ## this will replace the app's session handling
    #KVSessionExtension(store, app)

    #fun2say
    vpymongo.init_app(app, 
                    [{"name":"messages", "field":"text"}],
                    'FUNFUNSAY')
    fun2say.init_app(app, vpymongo.db)

    # cache
    cache.init_app(app)

    # babel
    #print "create babel object"
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        # if a user is logged in, use the locale from the user settings
        if current_user.is_authenticated():
            return current_user.locale
        # otherwise try to guess the language from the user accept
        # header the browser transmits.  We support de/fr/en in this
        # example.  The best match wins.
        return request.accept_languages.best_match(['zh_CN', 'en'])

    @babel.timezoneselector
    def get_timezone():
        if current_user.is_authenticated():
            return current_user.timezone
        return app.config['BABEL_DEFAULT_TIMEZONE']

    # login.
    from flask.ext.login import LoginManager
    login_manager = LoginManager()    
    login_manager.session_protection = None #@fixme!
    login_manager.login_view = 'homesite.login'
    login_manager.refresh_view = 'homesite.reauth'
    login_manager.login_message = _("Please log in to access this page.")

    @login_manager.user_loader
    def load_user(id):
        #print "####: loaduser ", id
        return User.load_user(id)
    login_manager.setup_app(app)

    from flask.ext.markdown import Markdown
    Markdown(app, safe_mode="escape")


def configure_blueprints(app, blueprints):
    """Configure blueprints in views."""

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


def configure_template_filters(app):
    @app.template_filter()
    def format_datetime(value):
        """Format a timestamp for display."""
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def configure_hook(app):
    @app.before_request
    def before_request():
        g.MAX_LEN_P = MAX_LEN_P
        g.db = vpymongo.db # a link to g.mongo.db to make it more convinient
        

    @app.teardown_request
    def teardown_request(exception):
        pass

    @app.after_request
    def after_request(response):
        #def record(sender, template, context, **extra):
        #    print "record:"
        #    if current_user.id:
        #        session_id = current_user.session_id if current_user.session_id else randbytes(8)
        #        response.set_cookie('user_id', "%s:%s" % (current_user.id, session_id))
        #        fun2say.api.update_user_profile(userid=current_user.id, session_id=session_id)
        #
        #    else:
        #        response.set_cookie('user_id', None)
        #
        #session_protected.connect(record, response)

        return response 
