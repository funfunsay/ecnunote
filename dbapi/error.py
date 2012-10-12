# Fun2say
# Copyright 2012 Brent Jiang
# See LICENSE for details.

class Fun2sayError(Exception):
    """Fun2say exception"""

    def __init__(self, reason, response=None):
        self.reason = unicode(reason)
        self.response = response

    def __str__(self):
        return self.reason

