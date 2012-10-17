# -*- coding: utf-8 -*-

from flask import (Blueprint, render_template, current_app, request,
                   flash, url_for, redirect, session, g, abort)
from werkzeug import (generate_password_hash, check_password_hash,
                      cached_property)
from flask.ext.login import (UserMixin, login_user, current_user, logout_user)
import pymongo
from bson.objectid import ObjectId
import time
from funfunsay.extensions import mongo

from funfunsay.utils import get_current_time, VARCHAR_LEN_128

class User(UserMixin):
    def __init__(self, userDoc=None, **kwargs):
        self.document = userDoc
        if self.document is not None:
            self.id = userDoc.id
            self.name = userDoc.name
            self.email = userDoc.email
            self.reg_date = userDoc.reg_date
            self.locale = userDoc.locale
            self.timezone = userDoc.timezone
            #self.session_id = userDoc.session_id
    
    document = None
    id = None
    name = None
    email = None
    _password = None
    activation_key = None
    followers = None
    following = None
    reg_date = None
    locale = 'zh_CH'
    timezone = 'Asia/Shanghai'
    session_id = None

    def __repr__(self):
        return '<User %r>' % self.name

    @classmethod
    def load_user(cls, userid):
        """
        used to load User Model derived from flask.ext.login.UserMixedIn
        """
        userDoc = current_app.dbapi.get_user_profile(id=userid)
        if current_app.dbapi.success:
            user = cls(userDoc)
            return user
        else:
            return None

    @classmethod
    def get_user_profile(cls, userid):
        """
        used to fetch other user's information
        """
        userDoc = current_app.dbapi.get_user_profile(id=userid)
        return userDoc

    #def _get_password(self):
    #    return self._password

    #def _set_password(self, password):
    #    self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    #password = property(_get_password, _set_password)

    #def check_password(self, password):
    #    if self.password is None:
    #        return False
    #    return check_password_hash(self.password, password)

    #@property
    #def num_followers(self):
    #    if self.followers:
    #        return len(self.followers)
    #    return 0

    #@property
    #def num_following(self):
    #    return len(self.following)

    #def follow(self, user):
    #    user.followers.add(self.id)
    #    self.following.add(user.id)

    #def unfollow(self, user):
    #    if self.id in user.followers:
    #        user.followers.remove(self.id)
    #
    #    if user.id in self.following:
    #        self.following.remove(user.id)

    #def get_following_query(self):
    #    return User.query.filter(User.id.in_(self.following or set()))

    #def get_followers_query(self):
    #    return User.query.filter(User.id.in_(self.followers or set()))

    def is_authenticated(self):
        return False if (self.document == None) else True

    @classmethod
    def new_document(cls, user_id, email, raw_passwd):
        """
        initialize a new user document
        """
        cur_time = int(time.time())
        user_doc = {"_id":user_id,
                    "email":email,
                    "pw_hash":generate_password_hash(raw_passwd),
                    "copyrights":"user",
                    "reg_date":cur_time,
                    'locale':'zh_CN',
                    'timezone': 'Asia/Shanghai',
                    'providers': [],

                    }
        return user_doc

    @classmethod
    def new_invitation_code_document(cls, user_id, code):
        cur_time = int(time.time())
        code_doc = {"code":code,
                    "author_id":user_id,
                    "used":'False', #become user_id after used
                    "create_time":cur_time,
                    "use_time":None
                    }
        return code_doc


    @classmethod
    def new_vote_document(cls, user_id, messageid, voteval):
        vote_doc = {'user_id':user_id,
                    'message_id':messageid,
                    'vote':voteval
                    }
        return vote_doc


    @classmethod
    def new_follower_document(cls, who_id, whom_id):
        follower_doc = {"who_id":who_id, 
                        "whom_id":whom_id }
        return follower_doc

    @classmethod
    def authenticate(cls, login, password):
        #print ": authenticate(cls, login, password):"
        error = None
        #print "mongo.db: ", mongo.db
        user_doc = current_app.dbapi.get_user_profile(login=login)

        if current_app.dbapi.success==True:
            authenticated = check_password_hash(user_doc.pw_hash, password)
            if not authenticated:
                error = 'Invalid password'
                user_doc = None
        else:
            error = 'Invalid username'
            authenticated = False
            return None, False, error

        #print user_doc
        #print authenticated
        #print error
        user = User(user_doc)
        return user, authenticated, error

    def is_active(self):
        return True

    @classmethod
    def search(cls, keywords):
        criteria = []
        for keyword in keywords.split():
            keyword = '%' + keyword + '%'
            criteria.append(db.or_(
                User.name.ilike(keyword),
                User.email.ilike(keyword),
            ))
        q = reduce(db.and_, criteria)
        return cls.query.filter(q)


    @classmethod
    def get_latest_message(cls, userid):
        return mongo.db.messages.find_one({"author_id":userid}, sort=[("pub_date", pymongo.DESCENDING)])

    def get_icon_url(self):
        #return self.get_profile().get("icon_url", "")
        return ''

    @classmethod
    def my_vote(cls, messageid):
        """
        return 0 if not voted, -1 means vote down, 1 means vote up
        """
        if not current_user.is_authenticated():
            return 0

        vote_doc = mongo.db.votes.find_one({'message_id':messageid, 'user_id':current_user.id})
        if vote_doc is None:
            return 0

        #print vote_doc
        return vote_doc['vote']


    @classmethod
    def do_vote(cls, messageid, voteval):
        """
        return 0 if not voted, -1 means vote down, 1 means vote up
        message_id: an ObjectId of message, voteval should be integer
        """
        #print messageid
        #print voteval
        if not current_user.is_authenticated():
            return 0

        message_doc = mongo.db.messages.find_one({'_id':messageid})

        # cannot vote self!
        if current_user.id == message_doc['author_id']:
            return 0, int(message_doc['score'])

        vote_doc = mongo.db.votes.find_one({'message_id':messageid, 'user_id':current_user.id})
        #print vote_doc
        if vote_doc is None:
            vote_doc = User.new_vote_document(current_user.id, messageid, voteval)
            mongo.db.votes.insert(vote_doc, safe=True)
            if voteval==1:
                message_doc['vote_up_count'] = message_doc['vote_up_count'] + 1
                message_doc['score'] = message_doc['score'] + 1
            else:
                message_doc['vote_down_count'] = message_doc['vote_down_count'] + 1
                message_doc['score'] = message_doc['score'] - 1
            mongo.db.messages.save(message_doc, safe=True)
            return voteval, int(message_doc['score'])

        if vote_doc['vote']<>voteval:
            if vote_doc['vote']==1:
                message_doc['vote_up_count'] = message_doc['vote_up_count'] - 1
                message_doc['vote_down_count'] = message_doc['vote_down_count'] + 1
                message_doc['score'] = message_doc['score'] - 2
            elif vote_doc['vote']==-1:
                message_doc['vote_up_count'] = message_doc['vote_up_count'] + 1
                message_doc['vote_down_count'] = message_doc['vote_down_count'] - 1
                message_doc['score'] = message_doc['score'] + 2

            vote_doc['vote'] = voteval
            mongo.db.votes.save(vote_doc, safe=True)
        else:
            if vote_doc['vote']==1:
                message_doc['vote_up_count'] = message_doc['vote_up_count'] - 1
                message_doc['score'] = message_doc['score'] - 1
            else:
                message_doc['vote_down_count'] = message_doc['vote_down_count'] - 1
                message_doc['score'] = message_doc['score'] + 1
            voteval = 0
            mongo.db.votes.remove(vote_doc, safe=True)

        mongo.db.messages.save(message_doc, safe=True)

        return voteval, int(message_doc['score'])