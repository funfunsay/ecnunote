# -*- coding: utf-8 -*-
# Fun2say
# Copyright 2012 Brent Jiang
# See LICENSE for details.

from fun2say.models import ModelFactory
from fun2say.utils import import_simplejson
from fun2say.error import Fun2sayError
import sys

class Parser(object):

    def parse(self, method, payload):
        """
        Parse the response payload and return the result.
        Returns a tuple that contains the result data and the cursors
        (or None if not present).
        """
        raise NotImplementedError

    def parse_error(self, payload):
        """
        Parse the error message from payload.
        If unable to parse the message, throw an exception
        and default error message will be used.
        """
        raise NotImplementedError


class RawParser(Parser):

    def __init__(self):
        pass

    def execute(self, method):
        method.api.clear()
        return ""

    def parse(self, method, payload):
        return payload

    def parse_error(self, payload):
        return payload


class JSONParser(Parser):

    payload_format = 'json'

    def __init__(self):
        self.json_lib = import_simplejson()

    def parse(self, method, payload):
        try:
            json = self.json_lib.loads(payload)
        except Exception, e:
            raise Fun2sayError('Failed to parse JSON payload: %s' % e)

        needsCursors = method.parameters.has_key('cursor')
        if needsCursors and isinstance(json, dict) and 'previous_cursor' in json and 'next_cursor' in json:
            cursors = json['previous_cursor'], json['next_cursor']
            return json, cursors
        else:
            return json

    def parse_error(self, payload):
        error = self.json_lib.loads(payload)
        if error.has_key('error'):
            return error['error']
        else:
            return error['errors']


class ModelParser(JSONParser):

    def __init__(self, model_factory=None):
        JSONParser.__init__(self)
        self.model_factory = model_factory or ModelFactory

    def execute(self, method):
        """generate mongodb requests and returns model objects

        This function is a combination of Fun2say's http-request and parse().
        """
        method.api.clear()
        try:
            if method.payload_type is None: return
            model = getattr(self.model_factory, method.payload_type)
        except AttributeError:
            raise Fun2sayError('No model for this payload type: %s' % method.payload_type)

        #@todo critical!: how to avoid dumps+loads while still remain
        #invoking parse()?
        #@todo-fixed: seems no need to fix now!
        payload = self.json_lib.dumps( model.handler(method.path, method.api, method.parameters) )

        return self.parse(method, payload)

    def parse(self, method, payload):
        try:
            if method.payload_type is None: return
            model = getattr(self.model_factory, method.payload_type)
        except AttributeError:
            raise Fun2sayError('No model for this payload type: %s' % method.payload_type)

        json = JSONParser.parse(self, method, payload)
        if isinstance(json, tuple):
            json, cursors = json
        else:
            cursors = None

        if method.payload_list:
            result = model.parse_list(method.api, json)
        else:
            result = model.parse(method.api, json)

        if cursors:
            return result, cursors
        else:
            return result

