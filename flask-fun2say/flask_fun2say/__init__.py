# Copyright (c) 2012, Brent Jiang
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
import pymongo 
import fun2say
from flask import current_app
from flask.ext.vpymongo import PyMongoV

__all__ = ('Fun2say',
           'ASCENDING', 'DESCENDING', 'MessageSortBasis',
           'UNSHARED', 'SHARED',
           'VISIBLE', 'REMOVED', 'REMOVED_ONLY',
           'NATURAL', 'ALPHABETICALLY', 'DATE_CREATED', 'DATE_MODIFIED', 'DATE_REMOVED', 'RATE_SCORE')


"""Python driver for FunFunSay Database."""


ASCENDING = pymongo.ASCENDING
"""Ascending sort order."""
DESCENDING = pymongo.DESCENDING
"""Descending sort order."""


version_tuple = (0, 1, 0)


def get_version_string():
    if version_tuple[-1] == '+':
        return '.'.join(map(str, version_tuple[:-1])) + '+'
    return '.'.join(map(str, version_tuple))

version = get_version_string()
"""Current version of Fun2say."""

MESSAGE_LIMITS = 25

class MessageShareState:
    UNSHARED       = 0 # both shared and unshared messages
    SHARED         = 1 # only shred messages

UNSHARED = MessageShareState.UNSHARED
SHARED = MessageShareState.SHARED

class MessageIncluding:
    VISIBLE         = 0 # only visible messages
    REMOVED         = 1 # both visible and removed
    REMOVED_ONLY    = 2 # only removed messages

VISIBLE = MessageIncluding.VISIBLE
REMOVED = MessageIncluding.REMOVED
REMOVED_ONLY = MessageIncluding.REMOVED_ONLY

class MessageSortBasis:
    NATURAL         = 0
    ALPHABETICALLY  = 1
    DATE_CREATED    = 2
    DATE_MODIFIED   = 3
    DATE_REMOVED    = 4
    RATE_SCORE      = 5
    #FOLLOWER_NUMBER = 6
    #COMMENT_NUMBER  = 7

NATURAL         = MessageSortBasis.NATURAL         
ALPHABETICALLY  = MessageSortBasis.ALPHABETICALLY  
DATE_CREATED    = MessageSortBasis.DATE_CREATED    
DATE_MODIFIED   = MessageSortBasis.DATE_MODIFIED   
DATE_REMOVED    = MessageSortBasis.DATE_REMOVED    
RATE_SCORE      = MessageSortBasis.RATE_SCORE      
#FOLLOWER_NUMBER = MessageSortBasis.FOLLOWER_NUMBER 
#COMMENT_NUMBER  = MessageSortBasis.COMMENT_NUMBER  


MESSAGE_SORT_BASIS_MAP = {
    # this handles defaulting to DATE_CREATED for us
    None: "pub_date",

    # alias the string names to the correct constants
    NATURAL: "_id",
    ALPHABETICALLY: "text",
    DATE_CREATED: "pub_date",
    DATE_MODIFIED: "modified_date",
    DATE_REMOVED: "__flask_vpymongo_removed_date",
    RATE_SCORE: "score",
    #FOLLOWER_NUMBER: "", #@todo
    #COMMENT_NUMBER: "", #@todo
}
"""used for get sort basis of string format"""


class Fun2say(object):
    """The :class:`~flask_fun2say.Fun2say` class configures and creates a
    :class:`fun2say.API` instance based on Flask configuration variables.
    Instantiating a :class:`~flask_fun2say.Fun2say` with no arguments does not
    configure the :class:`fun2say.API`, and will not be usable unless
    :meth:`Fun2say.init_app` is subsequently called.

    :param flask.Flask app: the Flask application to which this Fun2say
       should be attached
    :param str config_prefix: the configuration variable prefix
    """

    def __init__(self, app=None, database=None, config_prefix='FUN2SAY'):
        # this is overridden by init_app if app is supplied
        self.config_prefix = None

        if app is not None and database is not None:
            self.init_app(app, database, config_prefix)

    def init_app(self, app, database, config_prefix='FUN2SAY'):
        """Initialize this :class:`~flask_fun2say.Fun2say` if no arguments were
        given to the constructor. Accepts the same arguments as the
        constructor.

        :parameter:
          - database: an instance of :class:`~vpymongo.Database` for use by
            fun2say API. 
        """
        app.extensions.setdefault('fun2say', {})

        if config_prefix in app.extensions['fun2say']:
            raise Exception('duplicate config_prefix "%s"' % config_prefix)

        self.config_prefix = config_prefix
        #app.config.setdefault('%s_LIMIT' % config_prefix, 25)


        api = fun2say.API(database)

        app.extensions['fun2say'][config_prefix] = (database, api)

    @property
    def api(self):
        """Return the :class:`fun2say.API` object if Flask-Fun2say has been
        properly configured and initialized, else return None.
        """
        if self.config_prefix not in current_app.extensions['fun2say']:
            raise Exception('not initialized. did you forget to call init_app?')
        fun2says = current_app.extensions.get('fun2say', {})
        api = fun2says.get(self.config_prefix, (None))[1]
        return api

    #@property
    #def database(self):
    #    """The automatically created
    #    :class:`~flask_pymongo.wrappers.Connection` or
    #    :class:`~flask_pymongo.wrappers.ReplicaSetConnection`
    #    object.
    #    """
    #    if self.config_prefix not in current_app.extensions['fun2say']:
    #        raise Exception('not initialized. did you forget to call init_app?')
    #    return current_app.extensions['fun2say'][self.config_prefix][0]
