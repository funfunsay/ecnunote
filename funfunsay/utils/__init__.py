# -*- coding: utf-8 -*-
"""
    Utils has nothing to do with models and views.
"""

import time
from datetime import datetime
from hashlib import md5
from babel.dates import format_datetime as dtformat
from pytz import timezone
import random
import string

VARCHAR_LEN_128 = 128


def randbytes(bytes_):
    return ''.join(random.sample(string.ascii_letters + string.digits, bytes_))

def get_current_time():
    return datetime.utcnow()


def pretty_date(dt, default=None):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    Ref: https://bitbucket.org/danjac/newsmeme/src/a281babb9ca3/newsmeme/
    """

    if default is None:
        default = 'just now'

    now = datetime.utcnow()
    diff = now - dt

    periods = (
        (diff.days / 365, 'year', 'years'),
        (diff.days / 30, 'month', 'months'),
        (diff.days / 7, 'week', 'weeks'),
        (diff.days, 'day', 'days'),
        (diff.seconds / 3600, 'hour', 'hours'),
        (diff.seconds / 60, 'minute', 'minutes'),
        (diff.seconds, 'second', 'seconds'),
    )

    for period, singular, plural in periods:

        if not period:
            continue

        if period == 1:
            return u'%d %s ago' % (period, singular)
        else:
            return u'%d %s ago' % (period, plural)

    return default

def format_datetime(timestamp):
    """Format a timestamp for display."""
    eastern = timezone('Asia/Shanghai')
    return dtformat(datetime.utcfromtimestamp(timestamp), 'yyyy-M-d @ HH:mm', tzinfo=eastern)


def format_datetime_now():
    """Format a timestamp for display."""
    timestamp = int(time.time());
    eastern = timezone('Asia/Shanghai')
    return dtformat(datetime.utcfromtimestamp(timestamp), 'yyyy-M-d @ HH:mm', tzinfo=eastern)

def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'http://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)

