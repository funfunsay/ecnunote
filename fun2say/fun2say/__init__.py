# Fun2say
# Copyright 2012 Brent Jiang
# See LICENSE for details.
"""
Fun2say FunFunSay API library
"""
__version__ = '0.1'
__author__ = 'Brent Jiang'
__license__ = 'MIT'

from fun2say.models import Note, ModelFactory
from fun2say.error import Fun2sayError
from fun2say.api import API
from fun2say.cache import Cache, MemoryCache, FileCache
from fun2say.cursor import Cursor
import vpymongo


"""Python driver for FunFunSay Database."""

