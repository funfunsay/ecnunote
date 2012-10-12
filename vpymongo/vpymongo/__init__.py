# vPyMongo
# Copyright 2012 Brent Jiang
# See LICENSE for details.
import bson
from pymongo import (connection, replica_set_connection, database, collection)
from vpymongo.version import (is_version_controled, init_global_versions)

#import sys, traceback
import time

#for import *
__ALL__ = ('Collection', 'Connection', 
           'Database', 'ReplicaSetConnection'
           )


class Connection(connection.Connection):
    """Returns instances of :class:`vpymongo.Database` instead
    of :class:`pymongo.database.Database` when accessed with dot notation.
    """

    def __getattr__(self, name):
        attr = super(Connection, self).__getattr__(name)
        if isinstance(attr, database.Database):
            return Database(self, name)
        return attr

class ReplicaSetConnection(replica_set_connection.ReplicaSetConnection):
    """Returns instances of :class:`vpymongo.Database`
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


    def insert(self, doc_or_docs, manipulate=True,
               safe=False, check_keys=True, continue_on_error=False, **kwargs):
        """Insert a document(s) into this collection with a version number.

        If `manipulate` is ``True``, the document(s) are manipulated using
        any :class:`~pymongo.son_manipulator.SONManipulator` instances
        that have been added to this :class:`~pymongo.database.Database`.
        In this case an ``"_id"`` will be added if the document(s) does
        not already contain one and the ``"id"`` (or list of ``"_id"``
        values for more than one document) will be returned.
        If `manipulate` is ``False`` and the document(s) does not include
        an ``"_id"`` one will be added by the server. The server
        does not return the ``"_id"`` it created so ``None`` is returned.

        If `safe` is ``True`` then the insert will be checked for
        errors, raising :class:`~pymongo.errors.OperationFailure` if
        one occurred. Safe inserts wait for a response from the
        database, while normal inserts do not.

        Any additional keyword arguments imply ``safe=True``, and
        will be used as options for the resultant `getLastError`
        command. For example, to wait for replication to 3 nodes, pass
        ``w=3``.

        :Parameters:
          - `doc_or_docs`: a document or list of documents to be
            inserted
          - `manipulate` (optional): manipulate the documents before
            inserting?
          - `safe` (optional): check that the insert succeeded?
          - `check_keys` (optional): check if keys start with '$' or
            contain '.', raising :class:`~pymongo.errors.InvalidName`
            in either case
          - `continue_on_error` (optional): If True, the database will not stop
            processing a bulk insert if one fails (e.g. due to duplicate IDs).
            This makes bulk insert behave similarly to a series of single
            inserts, except lastError will be set if any insert fails, not just
            the last one. If multiple errors occur, only the most recent will
            be reported by :meth:`~pymongo.database.Database.error`.
          - `**kwargs` (optional): any additional arguments imply
            ``safe=True``, and will be used as options for the
            `getLastError` command

        .. note:: `continue_on_error` requires server version **>= 1.9.1**

        .. versionadded:: 2.1
           Support for continue_on_error.
        .. versionadded:: 1.8
           Support for passing `getLastError` options as keyword
           arguments.
        .. versionchanged:: 1.1
           Bulk insert works with any iterable

        .. mongodoc:: insert
        """
        #@faq: how to asynchronous?
        # print "use my insert"  # words printed!
        docs = doc_or_docs
        if isinstance(docs, dict):
            docs = [docs]

        if manipulate:
            docs = [self._Collection__database._fix_incoming(doc, self) for doc in docs]

        if is_version_controled(self._Collection__database, self.name):
            for doc in docs:
                #doc['__flask_vpymongo_version'] = get_new_version(self.database, self.name)
                doc['__flask_vpymongo_visible'] = 'visible'

        return super(Collection, self).insert(docs, False,
                                               safe, check_keys, continue_on_error, **kwargs)


    def remove(self, spec_or_id=None, safe=False, **kwargs):
        """Remove a document(s) from this collection. 
           now, Flask-vPyMongo only make deletion a change of the 
           value of collection.__flask_vpymongo_visible field 
           from "visible" to "deleted"

        .. warning:: Calls to :meth:`remove` should be performed with
           care, as removed data cannot be restored.

        If `safe` is ``True`` then the remove operation will be
        checked for errors, raising
        :class:`~pymongo.errors.OperationFailure` if one
        occurred. Safe removes wait for a response from the database,
        while normal removes do not.

        If `spec_or_id` is ``None``, all documents in this collection
        will be removed. This is not equivalent to calling
        :meth:`~pymongo.database.Database.drop_collection`, however,
        as indexes will not be removed.

        If `safe` is ``True`` returns the response to the *lastError*
        command. Otherwise, returns ``None``.

        Any additional keyword arguments imply ``safe=True``, and will
        be used as options for the resultant `getLastError`
        command. For example, to wait for replication to 3 nodes, pass
        ``w=3``.

        :Parameters:
          - `spec_or_id` (optional): a dictionary specifying the
            documents to be removed OR any other type specifying the
            value of ``"_id"`` for the document to be removed
          - `safe` (optional): check that the remove succeeded?
          - `**kwargs` (optional): any additional arguments imply
            ``safe=True``, and will be used as options for the
            `getLastError` command

        .. mongodoc:: remove
        """
        if is_version_controled(self._Collection__database, self.name):
            if spec_or_id is None:
                spec_or_id = {}

            if not isinstance(spec_or_id, dict):
                spec_or_id = {"_id": spec_or_id}

            if self.safe or kwargs:
                safe = True
                if not kwargs:
                    kwargs.update(self.get_lasterror_options())

            return self.update(spec_or_id, 
                               {"$set": 
                                {"__flask_vpymongo_visible":"removed", 
                                 "__flask_vpymongo_removed_date":int(time.time())}
                                },
                               safe=safe, **kwargs)

        else:
            return super(Collection, self).remove(spec_or_id, safe, **kwargs)




    def find_v(self, *args, **kwargs):
        """Query the database, no matter removed or visible messages
        """
        return super(Collection, self).find(*args, **kwargs)

    def find_one_v(self, spec_or_id=None, *args, **kwargs):
        """Get a single document from the database, 
        no matter removed or visible messages.
        """
        if spec_or_id is not None and not isinstance(spec_or_id, dict):
            spec_or_id = {"_id": spec_or_id}

        for result in self.find_v(spec_or_id, *args, **kwargs).limit(-1):
            return result
        return None


    def find(self, *args, **kwargs):
        """Query the database.

        The `spec` argument is a prototype document that all results
        must match. For example:

        >>> db.test.find({"hello": "world"})

        only matches documents that have a key "hello" with value
        "world".  Matches can have other keys *in addition* to
        "hello". The `fields` argument is used to specify a subset of
        fields that should be included in the result documents. By
        limiting results to a certain subset of fields you can cut
        down on network traffic and decoding time.

        Raises :class:`TypeError` if any of the arguments are of
        improper type. Returns an instance of
        :class:`~pymongo.cursor.Cursor` corresponding to this query.

        :Parameters:
          - `spec` (optional): a SON object specifying elements which
            must be present for a document to be included in the
            result set
          - `fields` (optional): a list of field names that should be
            returned in the result set ("_id" will always be
            included), or a dict specifying the fields to return
          - `skip` (optional): the number of documents to omit (from
            the start of the result set) when returning the results
          - `limit` (optional): the maximum number of results to
            return
          - `timeout` (optional): if True, any returned cursor will be
            subject to the normal timeout behavior of the mongod
            process. Otherwise, the returned cursor will never timeout
            at the server. Care should be taken to ensure that cursors
            with timeout turned off are properly closed.
          - `snapshot` (optional): if True, snapshot mode will be used
            for this query. Snapshot mode assures no duplicates are
            returned, or objects missed, which were present at both
            the start and end of the query's execution. For details,
            see the `snapshot documentation
            <http://dochub.mongodb.org/core/snapshot>`_.
          - `tailable` (optional): the result of this find call will
            be a tailable cursor - tailable cursors aren't closed when
            the last data is retrieved but are kept open and the
            cursors location marks the final document's position. if
            more data is received iteration of the cursor will
            continue from the last document received. For details, see
            the `tailable cursor documentation
            <http://www.mongodb.org/display/DOCS/Tailable+Cursors>`_.
          - `sort` (optional): a list of (key, direction) pairs
            specifying the sort order for this query. See
            :meth:`~pymongo.cursor.Cursor.sort` for details.
          - `max_scan` (optional): limit the number of documents
            examined when performing the query
          - `as_class` (optional): class to use for documents in the
            query result (default is
            :attr:`~pymongo.connection.Connection.document_class`)
          - `slave_okay` (optional): if True, allows this query to
            be run against a replica secondary.
          - `await_data` (optional): if True, the server will block for
            some extra time before returning, waiting for more data to
            return. Ignored if `tailable` is False.
          - `partial` (optional): if True, mongos will return partial
            results if some shards are down instead of returning an error.
          - `manipulate`: (optional): If True (the default), apply any
            outgoing SON manipulators before returning.
          - `network_timeout` (optional): specify a timeout to use for
            this query, which will override the
            :class:`~pymongo.connection.Connection`-level default
          - `read_preference` (optional): The read preference for
            this query.

        .. note:: The `manipulate` parameter may default to False in
           a future release.

        .. note:: The `max_scan` parameter requires server
           version **>= 1.5.1**

        .. mongodoc:: find
        """
        args2 = list(args)
        if is_version_controled(self._Collection__database, self.name):
            if(args2[0] == None):
                args2[0] = {}

            args2[0]['__flask_vpymongo_visible']='visible'

        return super(Collection, self).find(*tuple(args2), **kwargs)
