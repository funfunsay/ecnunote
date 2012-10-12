# Fun2say
# Copyright 2012 Brent Jiang
# See LICENSE for details.
import os
import mimetypes

from fun2say.binder import bind_api
from fun2say.error import Fun2sayError
from fun2say.parsers import ModelParser, RawParser
from fun2say.utils import list_to_csv
import vpymongo
from pymongo.objectid import ObjectId

# For import *
__all__ = ['API']



class API(object):
    """description of class"""

    def __init__(self, db,
            parser=None):
        """
        :parameter:
          - 'db': an instance of :class:`vpymongo.connection.Connection`
        """
        self.db = db
        self.parser = parser or ModelParser()
        self.clear()

    def clear(self):
        self._error = ""
        self._success = True

    @property
    def error(self):
        """
        contains the error information. usually a string.
        """
        return self._error

    @error.setter
    def error(self, value):
        self._error = value

    @property
    def success(self):
        """
        True or False.
        """
        return self._success

    @success.setter
    def success(self, value):
        self._success = value

    """
    Get app_key and app_secret of Funfunsay.com from providers.

    :parameters:
     - 'provider': the uri of provider website
     currently only support 'open.weibo.com' for SinaWeibo.
    """
    get_oauth2_key = bind_api(
        path = 'get_oauth2_key',
        payload_type = 'oauth2', payload_list = False,
        allowed_param = ['provider']
        )


    """
    """
    upsert_provider = bind_api(
        path = 'upsert_provider',
        payload_type = 'user', payload_list = False,
        allowed_param = ['user_id', 'provider', 
            # these 3 params for update whole profile
            'their_profile','access_token', 'expires_in', 
            # these 2 params for update state
            'next_count', 'next_cursor']
        )

    """
    remove_provider
    """
    remove_provider = bind_api(
        path = 'remove_provider',
        payload_type = 'user', payload_list = False,
        allowed_param = ['user_id', 'provider', 
            'user_id_provider']
        )


    """
    get user profile via id or email.

    @todo: currently not support log in via 3rd website's account.

    :parameters:
    - login: can be id or email
    """
    get_user_profile = bind_api(
        path = 'get_user_profile',
        payload_type = 'user', payload_list = False,
        allowed_param = ['login', 'id', 'email', 'password',
            'provider', 'user_id_provider']
        )


    """
    Provide interface to create/modify user account.
    When create a new user, default notes and threads will be 
    automatically created.

    :parameters:
     - 'upsert': 
       - True: add new user if not exists.
       - False: don't add user if not exists, set api.success = False.

     - 'new_password': all user management need provide password,
        while modify password need another password.
     - 'session_id': temporary for callback re-auth
    """
    update_user_profile = bind_api(
        path = 'update_user_profile',
        payload_type = 'user', payload_list = False,
        allowed_param = ['user_id', 'upsert', 'name', 'email',
                         'new_pw_hash', 'introduction', 
                         'invitation_code', 'locale', 'timezone',
                         'provider', 'user_id_provider']
        )


    """Returns the 20 most recent statuses posted from the authenticating 
    user. It’s also possible to request another user’s timeline 
    via the id parameter.

    :parameters:
      - (id or author_id or screen_name), 
      - since_id, 
      - max_id, 
      - count, 
      - page, 
      - sort: order_in_paper/date_created/date_modified/rate_score.
      - Boolean shared_only: False- get all notes, or True - return only shared
               notes 
      - string direction: 'ascending' or 'descending'
      - thread_id: 'None' for All Notes
      - lastIds: overrulled 'page' parameter. should get next to this ID
      - tags: "tag1|tag2|tag3|..."
    """
    user_timeline = bind_api(
        path = 'user_timeline',
        payload_type = 'note', payload_list = True,
        allowed_param = ['author_id', 'direction', 'host_id', 'sort',
                          'count', 'page', 'per_page', 'shared_only',
                          'thread_id', 'paper_id', "tags", 'lastIds',
                          'criteria',
                          ]
        )

    """ notes/get_one """
    get_one_note = bind_api(
        path = 'get_one_note',
        payload_type = 'note', 
        allowed_param = ['id']
        )

    """ notes/add """
    add_note = bind_api(
        path = 'add_note',
        payload_type = 'note', 
        allowed_param = ['author_id', 'source', 'host_id', 'lat', 'long', 'source', 
                         'place_id', 'thread_id', 'paper_id', 'shared',
                         'pub_date', 'provider', 'user_id_provider']
        )

    """ notes/update """
    update_note = bind_api(
        path = 'update_note',
        payload_type = 'note',
        allowed_param = ['id', 'host_id', 'lat', 'long', 'source', 'place_id', 'shared']
    )

    """ notes/delete """
    delete_note = bind_api(
        path = 'delete_note',
        payload_type = 'note',
        allowed_param = ['id']
    )

    """ notes/take_in """
    take_in_note = bind_api(
        path = 'take_in_note',
        payload_type = 'note',
        allowed_param = ['id', 'user_id']
    )

    """ notes/count """
    count_notes = bind_api(
        path = 'count_notes',
        payload_type = 'counter',
        allowed_param = ['host_id', 'author_id', 'shared_only',
                          'thread_id']
    )

    """ notes/threads """
    note_threads = bind_api(
        path = 'note_threads',
        payload_type = 'thread', payload_list = True,
        allowed_param = ['author_id']
    )

    """ notes/papers """
    get_papers = bind_api(
        path = 'get_papers',
        payload_type = 'paper', payload_list = True,
        allowed_param = ['author_id', 'shared_only', 'id', 'count']
    )

    """ notes/threads """
    add_thread = bind_api(
        path = 'add_thread',
        payload_type = 'thread',
        allowed_param = ['author_id', 'name', 'shared']
    )

    """ notes/threads """
    update_thread = bind_api(
        path = 'update_thread',
        payload_type = 'thread',
        allowed_param = ['id', 'name', 'shared']
    )

    """ notes/threads """
    delete_thread = bind_api(
        path = 'delete_thread',
        payload_type = 'thread',
        allowed_param = ['id']
    )

    """ notes/threads """
    set_threads = bind_api(
        path = 'set_threads',
        payload_type = 'note',
        allowed_param = ['id', 'threads']
    )
    #@faq: how to pass array to this api interface?

    """ notes/papers """
    add_paper = bind_api(
        path = 'add_paper',
        payload_type = 'paper',
        allowed_param = ['author_id', 'name', 'shared']
    )

    """ notes/papers """
    delete_paper = bind_api(
        path = 'delete_paper',
        payload_type = 'paper',
        allowed_param = ['id']
    )

    """ papaers/update """
    update_paper = bind_api(
        path = 'update_paper',
        payload_type = 'paper',
        allowed_param = ['id', 'name', 'shared']
    )

    """ notes/papers """
    set_papers = bind_api(
        path = 'set_papers',
        payload_type = 'note',
        allowed_param = ['id', 'papers']
    )
    #@faq: how to pass array to this api interface?

    """ notes/papers """
    change_order = bind_api(
        path = 'change_order',
        payload_type = 'paper',
        allowed_param = ['start_pos', 'stop_pos', 'id', 'author_id']
    )


    """ tasks/syncm """
    get_syncm_tasks = bind_api(
        path = 'get_syncm_tasks',
        payload_type = 'syncmtask', payload_list = True,
        allowed_param = ['count']
        )

    """ tasks/syncm 
    :parameters:
    - :next_cursor: "0"(default) if first, otherwise idstr of the last 
    content
    """
    add_sync_task = bind_api(
        path = 'add_sync_task',
        payload_type = 'syncmtask', payload_list = False,
        allowed_param = ['provider', 'user_id', 'user_id_provider']
        )

    """
    """
    get_sync_tasks = bind_api(
        path = 'get_sync_tasks',
        payload_type = 'syncmtask', payload_list = True,
        allowed_param = ['provider', 'user_id', 'user_id_provider',
            'state']
        )

    """
    """
    start_sync_task = bind_api(
        path = 'start_sync_task',
        payload_type = 'syncmtask', payload_list = False,
        allowed_param = ['provider', 'user_id', 'user_id_provider']
        )

    """
    """
    finish_sync_task = bind_api(
        path = 'finish_sync_task',
        payload_type = 'syncmtask', payload_list = False,
        allowed_param = ['provider', 'user_id', 'user_id_provider']
        )

    """
    website access control
    """
    check_request_interval = bind_api(
        path = 'check_request_interval',
        payload_type = 'webac', payload_list = False,
        allowed_param = ['ip']
        )
