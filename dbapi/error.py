# Dbapi
# Copyright 2012 Brent Jiang
# See LICENSE for details.

class DbapiError(Exception):
    """Dbapi exception"""

    def __init__(self, reason, response=None):
        self.reason = unicode(reason)
        self.response = response

    def __str__(self):
        return self.reason

