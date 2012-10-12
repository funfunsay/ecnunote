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


__all__ = ('PyMongoV', 'ASCENDING', 'DESCENDING', 'PRIMARY',
           'SECONDARY', 'SECONDARY_ONLY', 'HEAD')

import bson
from flask import abort, request
from gridfs import GridFS, NoFile
from mimetypes import guess_type
from pymongo import ReadPreference, ASCENDING, DESCENDING
from werkzeug.wsgi import wrap_file
from werkzeug.routing import BaseConverter

from flask_vpymongo.wrappers import Connection
from flask_vpymongo.wrappers import ReplicaSetConnection
from vpymongo.version import init_global_versions


PRIMARY = ReadPreference.PRIMARY
"""Send all queries to the replica set primary, and fail if none exists."""

SECONDARY = ReadPreference.SECONDARY
"""Distribute queries among replica set secondaries unless none exist or
are up, in which case send queries to the primary."""

SECONDARY_ONLY = ReadPreference.SECONDARY_ONLY
"""Distribute queries among replica set secondaries, and fail if none
exist."""

DESCENDING = DESCENDING
"""Descending sort order."""

ASCENDING = ASCENDING
"""Ascending sort order."""

READ_PREFERENCE_MAP = {
    # this handles defaulting to PRIMARY for us
    None: PRIMARY,

    # alias the string names to the correct constants
    'PRIMARY': PRIMARY,
    'SECONDARY': SECONDARY,
    'SECONDARY_ONLY': SECONDARY_ONLY,
}


class BSONObjectIdConverter(BaseConverter):
    """A simple converter for the RESTful URL routing system of Flask.

    .. code-block:: python

        @app.route('/<ObjectId:task_id>')
        def show_task(task_id):
            task = mongo.db.tasks.find_one_or_404(task_id)
            return render_template('task.html', task=task)

    It checks the validate of the id and converts it into a
    :class:`~bson.objectid.ObjectId` object. The converter will be
    automatically registered by the initialization of
    :class:`~flask_vpymongo.PyMongoV` with keyword :attr:`ObjectId`.
    """

    def to_python(self, value):
        try:
            return bson.ObjectId(value)
        except bson.errors.InvalidId:
            raise abort(400)

    def to_url(self, value):
        return str(value)


class PyMongoV(object):
    """Automatically connects to MongoDB using parameters defined in Flask
    configuration named ``MONGO_HOST``, ``MONGO_PORT``, and ``MONGO_DBNAME``.
    """

    def __init__(self, app=None, v_collections=[], config_prefix='MONGO'):
        if app is not None:
            self.init_app(app, v_collections, config_prefix)

    def init_app(self, app, v_collections=[], config_prefix='MONGO'):
        """Initialize the `app` for use with this :class:`~PyMongoV`. This is
        called automatically if `app` is passed to :meth:`~PyMongoV.__init__`.

        The app is configured according to the configuration variables
        ``PREFIX_HOST``, ``PREFIX_PORT``, ``PREFIX_DBNAME``,
        ``PREFIX_REPLICA_SET``, ``PREFIX_READ_PREFERENCE``,
        ``PREFIX_USERNAME``, and ``PREFIX_PASSWORD`` where "PREFIX"
        defaults to "MONGO".

        :param flask.Flask app: the application to configure for use with
           this :class:`~PyMongoV`
        :param array v_collections: array of dicts of collections that need to 
           be version controled. the dict consists of collections's "name",
           collections's "field" for version control 
        :param str config_prefix: determines the set of configuration
           variables used to configure this :class:`~PyMongoV`
        """
        self._app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        if 'vpymongo' not in app.extensions:
            app.extensions['vpymongo'] = {}

        if config_prefix in app.extensions['vpymongo']:
            raise Exception('duplicate config_prefix "%s"' % config_prefix)

        self.config_prefix = config_prefix

        app.config.setdefault('%s_HOST' % config_prefix, 'localhost')
        app.config.setdefault('%s_PORT' % config_prefix, 27017)
        app.config.setdefault('%s_DBNAME' % config_prefix, app.name)
        app.config.setdefault('%s_READ_PREFERENCE' % config_prefix, None)

        # these don't have defaults
        app.config.setdefault('%s_USERNAME' % config_prefix, None)
        app.config.setdefault('%s_PASSWORD' % config_prefix, None)
        app.config.setdefault('%s_REPLICA_SET' % config_prefix, None)

        username = app.config['%s_USERNAME' % config_prefix]
        password = app.config['%s_PASSWORD' % config_prefix]
        auth = (username, password)

        if any(auth) and not all(auth):
            raise Exception('Must set both USERNAME and PASSWORD or neither')

        read_preference = app.config['%s_READ_PREFERENCE' % config_prefix]
        read_preference = READ_PREFERENCE_MAP.get(read_preference)
        if read_preference not in (PRIMARY, SECONDARY, SECONDARY_ONLY):
            raise Exception('"%s_READ_PREFERENCE" must be one of '
                            'PRIMARY, SECONDARY, SECONDARY_ONLY'
                            % config_prefix)

        replica_set = app.config['%s_REPLICA_SET' % config_prefix]

        host = app.config['%s_HOST' % config_prefix]
        port = app.config['%s_PORT' % config_prefix]
        try:
            port = int(port)
        except ValueError:
            raise TypeError('%s_PORT must be an integer' % config_prefix)

        dbname = app.config['%s_DBNAME' % config_prefix]

        args = []
        kwargs = {
            'host': host,
            'port': port,
            'read_preference': read_preference,
            'tz_aware': True,
            'safe': True,
        }

        if replica_set is not None:
            args.append('%s:%d' % (host, port))
            del kwargs['host']
            del kwargs['port']
            kwargs['replicaSet'] = replica_set
            connection_cls = ReplicaSetConnection
        else:
            connection_cls = Connection

        cx = connection_cls(*args, **kwargs)
        db = cx[dbname]

        if any(auth):
            db.authenticate(username, password)

        app.extensions['vpymongo'][config_prefix] = (cx, db)
        app.url_map.converters['ObjectId'] = BSONObjectIdConverter

        # set up hooks
        if replica_set is None:
            def call_end_request(response):
                cx.end_request()
                return response
            app.after_request(call_end_request)

        # init version control collections
        if len(v_collections) > 0:
            for c in v_collections:
                init_global_versions(db, c)


    @property
    def cx(self):
        """The automatically created
        :class:`~flask_pymongo.wrappers.Connection` or
        :class:`~flask_pymongo.wrappers.ReplicaSetConnection`
        object.
        """
        if self.config_prefix not in self._app.extensions['vpymongo']:
            raise Exception('not initialized. did you forget to call init_app?')
        return self._app.extensions['vpymongo'][self.config_prefix][0]

    @property
    def db(self):
        """The automatically created
        :class:`~flask_pymongo.wrappers.Database` object
        corresponding to the provided ``MONGO_DBNAME`` configuration
        parameter.
        """
        #print current_app.extensions['vpymongo']
        #print self.config_prefix
        if self.config_prefix not in self._app.extensions['vpymongo']:
            raise Exception('not initialized. did you forget to call init_app?')
        return self._app.extensions['vpymongo'][self.config_prefix][1]

    # view helpers
    def send_file(self, filename, base='fs', version=-1, cache_for=31536000):
        """Return an instance of the :attr:`~flask.Flask.response_class`
        containing the named file, and implement conditional GET semantics
        (using :meth:`~werkzeug.wrappers.ETagResponseMixin.make_conditional`).

        .. code-block:: python

            @app.route('/uploads/<path:filename>')
            def get_upload(filename):
                return mongo.send_file(filename)

        :param str filename: the filename of the file to return
        :param str base: the base name of the GridFS collections to use
        :param bool version: if positive, return the Nth revision of the file
           identified by filename; if negative, return the Nth most recent
           revision. If no such version exists, return with HTTP status 404.
        :param int cache_for: number of seconds that browsers should be
           instructed to cache responses
        """
        if not isinstance(base, (str, unicode)):
            raise TypeError('"base" must be string or unicode')
        if not isinstance(version, (int, long)):
            raise TypeError('"version" must be an integer')
        if not isinstance(cache_for, (int, long)):
            raise TypeError('"cache_for" must be an integer')

        storage = GridFS(self.db, base)

        try:
            fileobj = storage.get_version(filename=filename, version=version)
        except NoFile:
            abort(404)


        # mostly copied from flask/helpers.py, with
        # modifications for GridFS
        data = wrap_file(request.environ, fileobj, buffer_size=1024*256)
        response = current_app.response_class(
            data,
            mimetype=fileobj.content_type,
            direct_passthrough=True)
        response.content_length = fileobj.length
        response.last_modified = fileobj.upload_date
        response.set_etag(fileobj.md5)
        response.cache_control.max_age = cache_for
        response.cache_control.s_max_age = cache_for
        response.cache_control.public = True
        response.make_conditional(request)
        return response

    def save_file(self, filename, fileobj, base='fs', content_type=None):
        """Save the file-like object to GridFS using the given filename.
        Returns ``None``.

        .. code-block:: python

            @app.route('/uploads/<path:filename>', methods=['POST'])
            def save_upload(filename):
                mongo.save_file(filename, request.files['file'])
                return redirect(url_for('get_upload', filename=filename))

        :param str filename: the filename of the file to return
        :param file fileobj: the file-like object to save
        :param str base: base the base name of the GridFS collections to use
        :param str content_type: the MIME content-type of the file. If
           ``None``, the content-type is guessed from the filename using
           :func:`~mimetypes.guess_type`
        """
        if not isinstance(base, (str, unicode)):
            raise TypeError('"base" must be string or unicode')
        if not (hasattr(fileobj, 'read') and callable(fileobj.read)):
            raise TypeError('"fileobj" must have read() method')

        if content_type is None:
            content_type, _ = guess_type(filename)

        storage = GridFS(self.db, base)
        storage.put(fileobj, filename=filename, content_type=content_type)

