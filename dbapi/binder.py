# Fun2say
# Copyright 2012 Brent Jiang
# See LICENSE for details.

import time
import re

from fun2say.error import Fun2sayError
from fun2say.utils import convert_to_utf8_str
from fun2say.models import Model


def bind_api(**config):

    class APIMethod(object):

        path = config['path']
        payload_type = config.get('payload_type', None)
        payload_list = config.get('payload_list', False)
        allowed_param = config.get('allowed_param', [])

        def __init__(self, api, args, kargs):
            self.api = api
            self.post_data = kargs.pop('post_data', None)
            self.build_parameters(args, kargs)

        def build_parameters(self, args, kargs):
            self.parameters = {}
            for idx, arg in enumerate(args):
                if arg is None:
                    continue

                try:
                    self.parameters[self.allowed_param[idx]] = convert_to_utf8_str(arg)
                except IndexError:
                    raise Fun2sayError('Too many parameters supplied!')

            for k, arg in kargs.items():
                if arg is None:
                    continue
                if k in self.parameters:
                    raise Fun2sayError('Multiple values for parameter %s supplied!' % k)

                self.parameters[k] = convert_to_utf8_str(arg)

        def execute(self):
            result = self.api.parser.execute(self)

            return result


    def _call(api, *args, **kargs):

        method = APIMethod(api, args, kargs)
        return method.execute()


    # Set pagination mode
    if 'cursor' in APIMethod.allowed_param:
        _call.pagination_mode = 'cursor'
    elif 'page' in APIMethod.allowed_param:
        _call.pagination_mode = 'page'

    return _call

