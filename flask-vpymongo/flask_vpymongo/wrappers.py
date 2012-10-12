# Copyright (c) 2011, Dan Crosta
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

from vpymongo import collection
from vpymongo import connection
from vpymongo import database
from vpymongo import replica_set_connection

from flask import abort

#import sys, traceback
import time

class Connection(connection.Connection):
    """Returns instances of :class:`flask_pymongo.wrappers.Database` instead
    of :class:`pymongo.database.Database` when accessed with dot notation.
    """

    def __getattr__(self, name):
        attr = super(Connection, self).__getattr__(name)
        if isinstance(attr, database.Database):
            return Database(self, name)
        return attr

class ReplicaSetConnection(replica_set_connection.ReplicaSetConnection):
    """Returns instances of :class:`flask_pymongo.wrappers.Database`
    instead of :class:`pymongo.database.Database` when accessed with dot
    notation.  """

    def __getattr__(self, name):
        attr = super(ReplicaSetConnection, self).__getattr__(name)
        if isinstance(attr, database.Database):
            return Database(self, name)
        return attr

class Database(database.Database):
    """Returns instances of :class:`vpymongo.Collection`
    instead of :class:`pymongo.collection.Collection` when accessed with dot
    notation.

    If there is , 
    returns instances of :class:`vpymongo.Collection`
    """

    def __getattr__(self, name):
        attr = super(Database, self).__getattr__(name)
        #print "attr:", attr
        if isinstance(attr, collection.Collection):
            return Collection(self, name)
        return attr

    def register_v(self, name):
        """register a collection to be version controled

        :Parameters:
          - `name`: name of a collection to be registered
        """
        init_global_versions(self, {"name":name,"field":None})


class Collection(collection.Collection):
    """Custom sub-class of :class:`pymongo.collection.Collection` which
    adds Flask-specific helper methods.
    """

    def __getattr__(self, name):
        attr = super(Collection, self).__getattr__(name)
        if isinstance(attr, Collection):
            # replace collection.Collection with a Collection 
            db = self._Collection__database
            return Collection(db, attr.name)
        return attr

