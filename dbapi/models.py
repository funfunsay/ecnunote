# -*- coding: utf-8 -*-
# Dbapi
# Copyright 2012 Brent Jiang
# See LICENSE for details.

# !!! IMPORTANT NOTICE !!!
# Must use dict.get(<field-name>, <default-value>) instead of 
# dict[<field-name>] when fetching data from handler.parameters
# 
# 2012-04-19
# - add html escape/unescape 

import pymongo
from bson.objectid import ObjectId
import time
import sys
from dbapi.error import DbapiError
from dbapi.utils import parse_datetime, parse_html_value, parse_a_href, \
        parse_search_datetime, unescape_html
from dbapi.utils.escape import (xhtml_escape, 
    xhtml_unescape, json_decode, json_encode)

from funfunsay.extensions import mongo

## test for not unescape
def source_unescape(str):
    return str
def source_escape(str):
    return str

class ResultSet(list):
    """A list like object that holds results from a Flask-Dbapi API query."""


class Model(object):

    def __init__(self, api=None):
        self._api = api

    def __getstate__(self):
        # pickle
        pickle = dict(self.__dict__)
        try:
            del pickle['_api']  # do not pickle the API reference
        except KeyError:
            pass
        return pickle

    @classmethod
    def _get_handler(cls, name):
        try:
            return getattr(cls, name)
        except AttributeError as e:
            #print e
            return None

    @classmethod
    def handler(cls, path, api, parameters):
        """
        @todo: improve efficiency 
        """
        handlers = {'add_note': cls._get_handler('add'),
            'user_timeline': cls._get_handler('query'),
            'update_note':cls._get_handler('update'),
            'delete_note':cls._get_handler('remove'),
            'get_one_note':cls._get_handler('query'),
            'take_in_note':cls._get_handler('take_in_note'),
            'count_notes':cls._get_handler('count_notes'),
            'note_threads':cls._get_handler('query'),
            'get_papers':cls._get_handler('query'),
            'add_thread':cls._get_handler('add'),
            'update_thread':cls._get_handler('update'),
            'delete_thread':cls._get_handler('remove'),
            'add_paper':cls._get_handler('add'),
            'update_paper':cls._get_handler('update'),
            'delete_paper':cls._get_handler('remove'),
            'set_papers':cls._get_handler('set_papers'),
            'set_threads':cls._get_handler('set_threads'),
            'change_order':cls._get_handler('change_order'),

            #user
            'get_user_profile':cls._get_handler('get_user_profile'),
            'update_user_profile':cls._get_handler('update_user_profile'),
            'add_sync_task':cls._get_handler('add_sync_task'),
            'get_sync_tasks':cls._get_handler('get_sync_tasks'),
            'start_sync_task':cls._get_handler('start_sync_task'),
            'finish_sync_task':cls._get_handler('finish_sync_task'),

            #oauth
            'get_oauth2_key':cls._get_handler('get_key'),
            'upsert_provider':cls._get_handler('upsert_provider'),
            'remove_provider':cls._get_handler('remove_provider'),

            #Website access control
            'check_request_interval':cls._get_handler('check_request_interval'),
            }
            
        obj = handlers[path](api, parameters)
        return obj

    @classmethod
    def query(cls, api, parameters):
        """Query database and generate a payload contains JSON objects."""
        raise NotImplementedError

    @classmethod
    def parse(cls, api, json):
        """Parse a JSON object into a model instance."""
        raise NotImplementedError

    @classmethod
    def parse_list(cls, api, json_list):
        """Parse a list of JSON objects into a result set of model instances."""
        ##print "parse_list:", json_list
        results = ResultSet()
        for obj in json_list:
            if obj:
                results.append(cls.parse(api, obj))
        return results


class Note(Model):

    @classmethod
    def _gen_model(cls, doc):
        modelDict = {}
        modelDict['author_id'] = doc['author_id']
        modelDict['shared'] = doc["shared"]
        modelDict['source'] =  source_unescape(doc['text'])
        modelDict['modified_date'] = doc['modified_date']
        modelDict['id'] = str(doc["_id"])
        modelDict["take_in_id"] = doc["take_in_id"]
        modelDict['host_id'] = doc['host_id']
        modelDict['papers'] = ""
        for paper in doc['papers']:
            modelDict['papers'] += paper['id'] + '&'
        modelDict['threads'] = ""
        for thread in doc['threads']:
            modelDict['threads'] += thread['id'] + '&'

        # for provider
        modelDict["provider"] = doc["provider"]
        modelDict["user_id_provider"] = doc["user_id_provider"]
        return modelDict

    @classmethod
    def add(cls, api, parameters):
        """handler method for add_note"""
        #print "note add: parameters:", parameters
        curTime = int(time.time())

        authorId = parameters.get('author_id', "")
        if authorId=="":
            raise DbapiError("Must specify 'author_id' to add_note!")

        source = parameters.get('source', "")
        if source=="":
            raise DbapiError("Must specify 'source' to add_note!")

        shared = True if parameters.get('shared', "False")=="True" else False

        hostId = parameters.get('host_id', None)

        threadId = parameters.get('thread_id', "")
        paperId = parameters.get('paper_id', "")

        pubDate = int(parameters.get('pub_date', curTime))
        provider = parameters.get('provider', 'www.ECNU')
        userIdProvider = parameters.get('user_id_provider', None)

        #print paperId
        paperDoc=None
        if paperId!="":
            paperDoc = mongo.db.papers.find_one({"_id":ObjectId(paperId)})

        doc = {"author_id":authorId, 
            "text":source_escape(source),
            "pub_date":pubDate,
            "books":[{"book_id":None, # belongs to which Twitterbook
                "order":0, # "None"(*), else 1, 2, 3, .... '0' is not used.
                }],
            "host_id":hostId, # belongs to which Message
            "take_in_id":'',
            "score":0,
            "vote_up_count":0,
            "vote_down_count":0, #
            "class":"note", #"note"(*), "principle" or "microblog"
            "threads":[] if threadId=="" else [{"id":threadId }],
            "papers":[] if paperId=="" else [{"id":paperId, "order":len(paperDoc["notes"])+1}],
            "modified_date":pubDate,
            "shared":shared,
            "visibility":"visible", #visible(*), hidden. Hidden if message(with host_id=None) was deleted
            "provider": provider,
            "user_id_provider": userIdProvider,
            }

        ids = mongo.db.messages.insert(doc)
        if paperId!="":
            paperDoc = mongo.db.papers.find_one({"_id":ObjectId(paperId)})
            paperDoc["notes"].append({"id":str(ids), "order":len(paperDoc["notes"])+1})
            paperDoc["modified_date"] = pubDate
            mongo.db.papers.save(paperDoc)

        doc["_id"] = ids

        return cls._gen_model(doc)

    @classmethod
    def update(cls, api, parameters):
        """handler method for update_note"""
        #print "note update: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise DbapiError("Note ID must provided for update!")

        doc = mongo.db.messages.find_one({"_id":ObjectId(noteId)})
        if doc == None:
            raise DbapiError("Cannot find the note to be updated!")

        shared = parameters.get('shared', None)
        #print "shared:", shared
        if shared!=None:
            doc["shared"] = True if shared=="True" else False
        
        doc['modified_date'] = int(time.time())

        source = parameters.get("source", "")
        if source!="":
            doc["text"] = source_escape(source)
        doc["host_id"] = parameters.get("host_id", doc["host_id"])

        status = mongo.db.messages.update({"_id":ObjectId(noteId)},
                                        doc, upsert=False, safe=True)

        return cls._gen_model(doc)


    @classmethod
    def attach_note_to_paper(cls, api, paperid, noteid):
        #print "attach_note_to_paper ", noteid
        paperDoc = mongo.db.papers.find_one({"_id": ObjectId(paperid)})
        if paperDoc == None:
            #raise DbapiError("Cannot find the paper to be updated!")
            #don't raise error: maybe ...
            return

        #print paperDoc
        for order in paperDoc['notes']:
            if order['id'] == noteid:
                #print "return =="
                return order['order']
        
        order = len(paperDoc['notes'])+1
        paperDoc["modified_date"] = int(time.time())
        mongo.db.papers.update({"_id":ObjectId(paperid)},
            paperDoc, upsert=False, safe=True)
        mongo.db.papers.update({"_id":ObjectId(paperid)},
            {'$push':{'notes': {'id':noteid, 'order':order} }})

        return order


    @classmethod
    def detach_note_from_paper(cls, api, paperid, noteid):
        #print "detach_note_from_paper ", noteid
        paperDoc = mongo.db.papers.find_one({"_id": ObjectId(paperid)})
        if paperDoc == None:
            #raise DbapiError("Cannot find the paper to be updated!")
            # don't raise error: maybe the paper has been deleted!
            return

        notePos = 0
        for note in paperDoc['notes']:
            if note['id']==noteid:
                notePos = note['order']

        for note in paperDoc['notes']:
            if note['order']>notePos:
                note['order'] -= 1
                mongo.db.messages.update(
                    {'_id':ObjectId(note['id']), "papers":{"$elemMatch":{"id":paperid }}},
                    {'$inc':{"papers.$.order":-1}}
                    )

        #paperDoc['notes'][:] = [d for d in paperDoc['notes'] if d.get('id') != noteid]
        # update orders first
        paperDoc["modified_date"] = int(time.time())
        mongo.db.papers.update({"_id":ObjectId(paperid)},
            paperDoc, upsert=False, safe=True)
        # then pull
        mongo.db.papers.update({"_id":ObjectId(paperid)},
            {'$pull':{"notes": {"id":noteid }}})


    @classmethod
    def set_papers(cls, api, parameters):
        """handler method for set_papers"""
        #print "note set_papers: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise DbapiError("set note papers: note id must provide!")
        doc = mongo.db.messages.find_one({"_id":ObjectId(noteId)})
        if doc == None:
            raise DbapiError("Cannot find the note to be updated!")

        # must do detach before attach!
        oldPapers = mongo.db.papers.find({"notes": {"$elemMatch":{"id":noteId }}})
        for old in oldPapers:
            oldPaperId = str(old['_id'])
            if not oldPaperId  in oldPapers:
                cls.detach_note_from_paper(api, oldPaperId, noteId)

        doc["papers"] = []
        paperIds = [] if parameters["papers"]=='' else parameters["papers"].split('&')
        #print "paperIds:", paperIds

        for paperId in paperIds:
            order = cls.attach_note_to_paper(api, paperId, noteId)
            #print "order:", order
            if order!=None:
                doc["papers"].append({'id':paperId, 'order':order})

        status = mongo.db.messages.update({"_id":ObjectId(noteId)},
                                        doc, upsert=False, safe=True)

        return cls._gen_model(doc)


    @classmethod
    def set_threads(cls, api, parameters):
        """handler method for set_threads"""
        #print "note set_threads: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise DbapiError("set note threads: note id must provide!")

        doc = mongo.db.messages.find_one({"_id":ObjectId(noteId)})
        if doc == None:
            raise DbapiError("Cannot find the note to be updated!")

        doc["threads"] = []
        for thread in parameters["threads"].split('&'):
            doc["threads"].append({'id':thread})

        status = mongo.db.messages.update({"_id":ObjectId(noteId)},
            doc, upsert=False, safe=True)

        return cls._gen_model(doc)


    @classmethod
    def remove(cls, api, parameters):
        """handler method for delete_note"""
        #print "note remove: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise DbapiError("remove note: note id must provide!")

        noteDoc = mongo.db.messages.find_one({"_id":ObjectId(noteId)})
        if noteDoc == None:
            raise DbapiError("Cannot find the note to be removed!")
 
        ##remove note from all papers
        for paper in noteDoc["papers"]:
            cls.detach_note_from_paper(api, paper["id"], noteId)
       
        status = mongo.db.messages.remove({"_id":ObjectId(noteId)})

        return cls._gen_model(noteDoc)


    @classmethod
    def take_in_note(cls, api, parameters):
        """
        Update the content when take in more times.
        """
        noteId = parameters.get("id", "")
        if noteId=="":
            raise DbapiError("take in ntoe: note id must provided!")

        userId = parameters.get("user_id", "")
        if userId=="":
            raise DbapiError("user id must provided!")

        noteDoc = mongo.db.messages.find_one({"take_in_id":noteId, "author_id":userId})
        if noteDoc == None:
            noteDoc = mongo.db.messages.find_one({"_id":ObjectId(noteId)})
            if noteDoc == None:
                ## @todo: how if the user take in just when the author delete it??
                raise DbapiError("Cannot find the note to be taken in!")

            if userId != str(noteDoc["author_id"]):
                noteDoc["author_id"] = userId
                noteDoc["pub_date"] = int(time.time())
                noteDoc["take_in_id"] = str(noteDoc["_id"])
                noteDoc["_id"] = ObjectId()
                noteDoc["modified_date"] = noteDoc["pub_date"]
                noteDoc['threads'] = []
                noteDoc['papers'] = []
                noteDoc['host_id'] = None
                noteDoc['shared'] = False
                mongo.db.messages.save(noteDoc)
        #@todo: if user modified taken-in note, how?
        # so wont support it now! maybe later!
        #@fixed: now take-in notes are not allowed to be modified.
        # so just let user update the note when take-in again
        else:
            ## has taken, so update the content!
            updatedNoteDoc = mongo.db.messages.find_one({"_id":ObjectId(noteId)})
            if userId != str(updatedNoteDoc["author_id"]):
                noteDoc["text"] = updatedNoteDoc["text"]
                noteDoc["modified_date"] = updatedNoteDoc["modified_date"]
                mongo.db.messages.save(noteDoc)

        return cls._gen_model(noteDoc)
    
    @classmethod
    def _query_one(cls, api, parameters, id):
        """handler method for query_note.
        Query database and generate a payload contains JSON objects.

        This function is a combination of database query and self.parse()
        """
        #print "note query: parameters:", parameters
        noteDoc = mongo.db.messages.find_one({"_id":ObjectId(id)})
        if noteDoc==None:
            raise DbapiError("Query one note failed on id %s"%(id))

        return cls._gen_model(noteDoc)


    @classmethod
    def _notes_in_paper_order(cls, api, paperId, perPage, skip, shared_only, direction):
        ## 2012-4-19, brent jiang
        ## currently, mongodb doesn't support sort on positional operator
        ## the positional operator ($) is just for matching.
        ## see :https://jira.mongodb.org/browse/SERVER-4451
        ## This one might help as well: https://jira.mongodb.org/browse/SERVER-153
        ## so now work around via a new array to put
        ##
        ## @fixme: now, shared/unshared-order-problem seems note exists 
        ##  here! but if shared_only, each time it may not return all 'perPage'
        ## notes
        noteDocs = mongo.db.messages.find({"papers": {"$elemMatch":{"id":paperId}}})
        sortedDocs = [0] * perPage
        index = 0
        if direction==pymongo.ASCENDING:
            upperbound = skip+perPage #shared/unshared-order-problem
        else:
            if skip==0:
                skip=noteDocs.count()+1 # 'order' in mongodb is 1-based
            upperbound = skip-1
            skip = upperbound-perPage
        #print "paperId:", paperId, ", perPage:", perPage, ", skip:", skip, ", shared_only:", shared_only
        #print 'direction:', direction

        for note in noteDocs:
            if shared_only==True and note["shared"]==False:
                continue

            if index==perPage-1:
                break

            for notepaper in note["papers"]:
                if notepaper["order"]!=None and notepaper["id"] == paperId:
                    order = int(notepaper["order"])
                    if order<=skip or order>upperbound:
                        #skip these notes
                        continue

                    index = (order - 1) % perPage
                    sortedDocs[ index ] = note
                    break

        noteDocs = []
        for a in sortedDocs:
            if a==0:
                continue
            if direction==pymongo.ASCENDING:
                noteDocs.append( a )
            else:
                noteDocs.insert(0, a)

        return noteDocs
    
    @classmethod
    def query(cls, api, parameters):
        """handler method for query_note.
        Query database and generate a payload contains JSON objects.

        This function is a combination of database query and self.parse()

        @todo: query notes in paper only support sort in 'ascending' order now.
        """
        #print "note query: parameters:", parameters
        models = []
        spec = {}
        authorId = parameters.get('author_id', "")
        if authorId != "":
            spec["author_id"] = authorId

        id = parameters.get('id', "")
        if id!="":
            spec["_id"] = ObjectId(id)
            return cls._query_one(api, parameters, id)

        spec["host_id"] = parameters.get('host_id', None)
        
        shared_only = parameters.get('shared_only', None)
        if shared_only == "True":
            spec["shared"] = True
            shared_only = True
        else:
            shared_only = False

        threadId = parameters.get('thread_id', "")
        if threadId != "":
            spec["threads"] = {"$elemMatch":{"id":threadId }}

        paperId = parameters.get('paper_id', "")
        if paperId != "":
            if threadId != "":
                raise DbapiError("note query error: both paperId and threadId specified! ")
            spec["papers"] = {"$elemMatch":{"id":paperId }}

        tags = parameters.get('tags', "")
        if tags != "":
            pass 
        criteria = parameters.get('criteria', "")
        if criteria != "":
            #print "criteria:", criteria
            spec["text"] = "$where:this.find(criteria)!=-1";

        page = int(parameters.get('page', 1))
        perPage = int(parameters.get('per_page', 20))
        ## skipCount is used for AJAX fetch notes
        lastIds = parameters.get('lastIds', "")
        #print "lastIds:", lastIds
        
        direction = {'ascending': pymongo.ASCENDING,
                     'descending': pymongo.DESCENDING
                     }.get(parameters.get('direction', 'descending'),  
                           pymongo.DESCENDING)

        sort = {'date_created': '_id',
                'date_modified': 'modified_date',
                'date_removed': 'modified_date',
                'rate_score': 'score',
                'order_in_paper': 'papers.$.order',
                }.get(parameters.get('sort', 'date_created'),  '_id')

        if lastIds=="":
            if sort=='papers.$.order':
                noteDocs = cls._notes_in_paper_order(api, paperId, perPage, (page-1)*perPage, shared_only, direction)
            else:
                noteDocs = mongo.db.messages.find(spec, 
                    sort=[(sort, direction)]).skip((page-1)*perPage).limit(perPage)
        else:
            lastDoc = mongo.db.messages.find_one({"_id":ObjectId(lastIds)})
            if lastDoc == None:
                raise DbapiError("note query: last ids invalid!")

            if sort=='papers.$.order':
                skip = 0
                for singleitem in lastDoc["papers"]:
                    if singleitem["id"] == paperId:
                        skip = int(singleitem["order"])
                        break
                noteDocs = cls._notes_in_paper_order(api, paperId, perPage, skip, shared_only, direction)
            else:
                spec[sort]= {"$lt" if direction==pymongo.DESCENDING else "$gt": lastDoc[sort]}
                noteDocs = mongo.db.messages.find(spec, 
                    sort=[(sort, direction)]).limit(perPage)

        for noteDoc in noteDocs:
            modelDict = cls._gen_model(noteDoc)
            models.append(modelDict)

        return tuple(models)


    @classmethod
    def parse(cls, api, json):
        note = cls(api)
        #print json
        for k, v in json.items():

            # some additional formatters
            if k == 'user':
                user_model = getattr(api.parser.model_factory, 'user')
                user = user_model.parse(api, v)
                setattr(note, 'author', user)
                setattr(note, 'user', user)  # DEPRECATED
            #not parse datetime here because we originally use
            #jinja format_datetime filter
            #elif k == 'modified_date':
            #    setattr(note, k, parse_datetime(v))
            elif k == 'a_href':
                if '<' in v:
                    setattr(note, k, parse_html_value(v))
                    setattr(note, 'source_url', parse_a_href(v))
                else:
                    setattr(note, k, v)
                    setattr(note, 'source_url', None)
            else:
                setattr(note, k, v)
        
        return note

    def destroy(self):
        return self._api.destroy_status(self.id)

    def retweet(self):
        return self._api.retweet(self.id)

    def retweets(self):
        return self._api.retweets(self.id)

    def favorite(self):
        return self._api.create_favorite(self.id)


class Thread(Model):
    
    @classmethod
    def add(cls, api, parameters):
        #print "thread add: parameters:", parameters
        authorId = parameters.get("author_id", "")
        if authorId=="":
            raise DbapiError("Author ID doesn't provided for add thread")
        name = parameters.get("name", "")
        if name=="":
            raise DbapiError("Thread name doesn't provided for add thread")
        shared = parameters.get("shared", False)

        threadDoc = mongo.db.threads.find_one({"author_id":authorId, "name":name})
        if threadDoc == None:
            threadDoc = {}
            threadDoc["author_id"] = authorId
            threadDoc["name"] = name
            threadDoc["shared"] = shared
            threadDoc["_id"] = ObjectId(mongo.db.threads.insert(threadDoc))
        else:
            api.success = False
            api.error = "db: the same name exists in the threads collection"

        modelDict = {}
        modelDict['id'] = str(threadDoc["_id"])
        modelDict['name'] = threadDoc["name"]
        modelDict['shared'] = threadDoc["shared"]
        modelDict['author_id'] = threadDoc["author_id"]
        #print "modelDict:", modelDict
        return modelDict
    
    @classmethod
    def update(cls, api, parameters):
        #print "thread update: parameters:", parameters
        threadId = parameters.get("id", "")
        if threadId=="":
            raise DbapiError("Thread ID doesn't provided for update thread")
        name = parameters.get("name", "")
        shared = parameters.get("shared", None) #it's 'None'! not default 'False'

        threadDoc = mongo.db.threads.find_one({"_id":ObjectId(threadId)})
        if threadDoc == None:
            raise DbapiError("Thread with id %s doesn't exists" % threadId)

        if name!= "":
            threadDoc["name"] = name
        if shared!= None:
            threadDoc["shared"] = shared
        mongo.db.threads.update({"_id":ObjectId(threadId)}, 
            threadDoc, upsert=False, safe=True)
        modelDict = {}
        modelDict['id'] = str(threadDoc["_id"])
        modelDict['name'] = threadDoc["name"]
        modelDict['shared'] = threadDoc["shared"]
        modelDict['author_id'] = threadDoc["author_id"]
        return modelDict
    
    @classmethod
    def remove(cls, api, parameters):
        #print "thread remove: parameters:", parameters
        threadId = parameters.get("id", "")
        if threadId=="":
            raise DbapiError("Thread ID doesn't provided for update thread")

        threadDoc = mongo.db.threads.find_one({"_id":ObjectId(threadId)})
        if threadDoc == None:
            raise DbapiError("Thread with id %s doesn't exists" % threadId)
        mongo.db.threads.remove({"_id":ObjectId(threadId)})
        modelDict = {}
        modelDict['id'] = str(threadDoc["_id"])
        modelDict['name'] = threadDoc["name"]
        modelDict['shared'] = threadDoc["shared"]
        modelDict['author_id'] = threadDoc["author_id"]
        return modelDict
    
    @classmethod
    def query(cls, api, parameters):
        #print "thread query: parameters:", parameters
        authorId = parameters.get("author_id", "")
        if authorId=="":
            raise DbapiError("Author ID doesn't provided for query threads")

        threadDocs = mongo.db.threads.find({"author_id":authorId})

        models = []
        for threadDoc in threadDocs:
            modelDict = {}
            modelDict['id'] = str(threadDoc["_id"])
            modelDict['name'] = threadDoc["name"]
            modelDict['shared'] = threadDoc["shared"]
            modelDict['author_id'] = threadDoc["author_id"]
            models.append(modelDict)

        ##print "models:", models

        return tuple(models)

    @classmethod
    def parse(cls, api, json):
        thread = cls(api)
        for k, v in json.items():
            setattr(thread, k, v)
        
        return thread


class Paper(Model):
    
    @classmethod
    def add(cls, api, parameters):
        #print "paper add: parameters:", parameters
        authorId = parameters.get("author_id", "")
        if authorId=="":
            raise DbapiError("Author ID doesn't provided for add paper")
        name = parameters.get("name", "")
        if name=="":
            raise DbapiError("Paper name doesn't provided for add paper")
        shared = parameters.get("shared", None)
        shared = True if shared=="True" else False ## 'None' means "not share"
        curTime = int(time.time())

        paperDoc = mongo.db.papers.find_one({"author_id":authorId, "name":name})
        if paperDoc == None:
            paperDoc = {}
            paperDoc["author_id"] = authorId
            paperDoc["name"] = name
            paperDoc["shared"] = shared
            paperDoc["notes"] = []
            paperDoc["pub_date"] = curTime
            paperDoc["modified_date"] = curTime
            paperDoc["_id"] = ObjectId(mongo.db.papers.insert(paperDoc))
        else:
            api.success = False
            api.error = "db: the same name exists in papers collection."


        modelDict = {}
        modelDict['id'] = str(paperDoc["_id"])
        modelDict['name'] = paperDoc["name"]
        modelDict['shared'] = paperDoc["shared"]
        modelDict['author_id'] = paperDoc["author_id"]
        modelDict['pub_date'] = paperDoc["pub_date"]
        modelDict['modified_date'] = paperDoc["modified_date"]

        #print "modelDict:", modelDict
        return modelDict
    
    @classmethod
    def update(cls, api, parameters):
        #print "paper update: parameters:", parameters
        paperId = parameters.get("id", "")
        if paperId=="":
            raise DbapiError("Paper ID doesn't provided for update paper")
        name = parameters.get("name", "")
        shared = parameters.get("shared", None) #it's 'None'! not default 'False'
        shared = True if shared=="True" else False ## 'None' means "not share"

        paperDoc = mongo.db.papers.find_one({"_id":ObjectId(paperId)})
        if paperDoc == None:
            raise DbapiError("Paper with id %s doesn't exists" % paperId)

        curTime = int(time.time())

        if name!= "":
            paperDoc["name"] = name
        if shared!= None:
            paperDoc["shared"] = shared
            paperDoc["modified_date"] = curTime
        mongo.db.papers.update({"_id":ObjectId(paperId)}, 
            paperDoc, upsert=False, safe=True)
        modelDict = {}
        modelDict['id'] = str(paperDoc["_id"])
        modelDict['name'] = paperDoc["name"]
        modelDict['shared'] = paperDoc["shared"]
        modelDict['author_id'] = paperDoc["author_id"]
        modelDict['pub_date'] = paperDoc["pub_date"]
        modelDict['modified_date'] = paperDoc["modified_date"]
        return modelDict
    
    @classmethod
    def remove(cls, api, parameters):
        #print "paper remove: parameters:", parameters
        paperId = parameters.get("id", "")
        if paperId=="":
            raise DbapiError("Paper ID doesn't provided for update paper")

        paperDoc = mongo.db.papers.find_one({"_id":ObjectId(paperId)})
        if paperDoc == None:
            raise DbapiError("Thread with id %s doesn't exists" % paperId)
        mongo.db.papers.remove({"_id":ObjectId(paperId)})
        modelDict = {}
        modelDict['id'] = str(paperDoc["_id"])
        modelDict['name'] = paperDoc["name"]
        modelDict['shared'] = paperDoc["shared"]
        modelDict['author_id'] = paperDoc["author_id"]
        modelDict['pub_date'] = paperDoc["pub_date"]
        modelDict['modified_date'] = paperDoc["modified_date"]
        return modelDict
    
    @classmethod
    def query(cls, api, parameters):
        #print "paper query: parameters:", parameters
        spec={}
        id = parameters.get('id', "")
        if id!="":
            spec["_id"] = ObjectId(id)

        sharedOnly = parameters.get('shared_only', None)
        if sharedOnly == "True":
            spec["shared"]=True

        authorId = parameters.get("author_id", "")
        if authorId!="":
            spec["author_id"] = authorId

        paperId = parameters.get("paper_id", "")
        if paperId!="":
            spec["_id"] = ObjectId(paperId)

        count = int(parameters.get("count", 0))

        #print "spec:", spec

        paperDocs = mongo.db.papers.find(spec, sort=[("modified_date", pymongo.DESCENDING)]).limit(0)

        models = []
        for paperDoc in paperDocs:
            modelDict = {}
            modelDict['id'] = str(paperDoc["_id"])
            modelDict['name'] = paperDoc["name"]
            modelDict['shared'] = paperDoc["shared"]
            modelDict['author_id'] = paperDoc["author_id"]
            modelDict['pub_date'] = paperDoc["pub_date"]
            modelDict['modified_date'] = paperDoc["modified_date"]
            models.append(modelDict)

        #print "models:", models

        return tuple(models)
    

    @classmethod
    def change_order(cls, api, parameters):
        startPos = parameters.get('start_pos', None)
        if startPos==None:
            raise DbapiError("start_pos doesn't provided for query papers")
        startPos = int(startPos)
        stopPos = parameters.get('stop_pos', None)
        if stopPos==None:
            raise DbapiError("stop_pos doesn't provided for query papers")
        stopPos = int(stopPos)
        paperId = parameters.get('id', None)
        if paperId==None:
            raise DbapiError("paper id doesn't provided for query papers")
        authorId = parameters.get('author_id', None)
        if authorId==None:
            raise DbapiError("Author ID doesn't provided for query papers")

        max = startPos if startPos > stopPos else stopPos
        min = startPos if startPos < stopPos else stopPos
        incValue=1
        if startPos < stopPos:
            incValue = -1
            max += 1
            min += 1
        else:
            incValue = 1
        #print _("Position from %d to %d changed, inc %d, min %d, max %d"%(startPos, stopPos, incValue, min, max))
        #flash(_("Position from %d to %d changed"%(startPos, stopPos)))

        paperDoc = mongo.db.papers.find_one({"_id":ObjectId(paperId),
             "author_id":authorId});
        if paperDoc==None:
            raise DbapiError("Cannot find paper to change order")

        #print paperDoc
        #re-order in db
        for note in paperDoc['notes']:
            if note['order']==startPos:
                note['order'] = stopPos
                mongo.db.messages.update(
                    {'_id':ObjectId(note['id']), "papers":{"$elemMatch":{"id":paperId }}}, 
                    {'$set':{"papers.$.order":stopPos}}
                    )
            elif note['order']>=min and note['order']<max:
                note['order']+=incValue
                mongo.db.messages.update(
                    {'_id':ObjectId(note['id']), "papers":{"$elemMatch":{"id":paperId }}},
                    {'$inc':{"papers.$.order":incValue}}
                    )

        paperDoc["modified_date"] = int(time.time())
        status = mongo.db.papers.update({'_id':paperDoc['_id']}, paperDoc, upsert= False, safe = True)
        #print status

        modelDict = {}
        modelDict['id'] = str(paperDoc["_id"])
        modelDict['name'] = paperDoc["name"]
        modelDict['shared'] = paperDoc["shared"]
        modelDict['author_id'] = paperDoc["author_id"]
        modelDict['pub_date'] = paperDoc["pub_date"]
        modelDict['modified_date'] = paperDoc["modified_date"]
        return modelDict

    @classmethod
    def parse(cls, api, json):
        paper = cls(api)
        for k, v in json.items():
            setattr(paper, k, v)
        
        return paper


class List(Model):
    
    @classmethod
    def parse(cls, api, json):
        lst = List(api)
        for k,v in json.items():
            if k == 'user':
                setattr(lst, k, User.parse(api, v))
            else:
                setattr(lst, k, v)
        return lst

    @classmethod
    def parse_list(cls, api, json_list, result_set=None):
        results = ResultSet()
        for obj in json_list['lists']:
            results.append(cls.parse(api, obj))
        return results

    def update(self, **kargs):
        return self._api.update_list(self.slug, **kargs)

    def destroy(self):
        return self._api.destroy_list(self.slug)

    def timeline(self, **kargs):
        return self._api.list_timeline(self.user.screen_name, self.slug, **kargs)

    def add_member(self, id):
        return self._api.add_list_member(self.slug, id)

    def remove_member(self, id):
        return self._api.remove_list_member(self.slug, id)

    def members(self, **kargs):
        return self._api.list_members(self.user.screen_name, self.slug, **kargs)

    def is_member(self, id):
        return self._api.is_list_member(self.user.screen_name, self.slug, id)

    def subscribe(self):
        return self._api.subscribe_list(self.user.screen_name, self.slug)

    def unsubscribe(self):
        return self._api.unsubscribe_list(self.user.screen_name, self.slug)

    def subscribers(self, **kargs):
        return self._api.list_subscribers(self.user.screen_name, self.slug, **kargs)

    def is_subscribed(self, id):
        return self._api.is_subscribed_list(self.user.screen_name, self.slug, id)


class JSONModel(Model):

    @classmethod
    def parse(cls, api, json):
        return json


class IDModel(Model):

    @classmethod
    def parse(cls, api, json):
        if isinstance(json, list):
            return json
        else:
            return json['ids']


class OAuth2(Model):
    """
    store account information from other websites.
    """

    @classmethod
    def get_key(cls, api, parameters):
        """
        get app_key and app_secret
        """
        provider = parameters.get('provider', None)
        if provider == None:
            raise DbapiError("Must specify 'provider' to get_key")
        oauthDoc = mongo.db.oauths.find_one({'provider':provider})
        return {
                "provider":provider,
                "app_key":oauthDoc["app_key"], 
                "app_secret":oauthDoc["app_secret"],
                "redirect_uri":oauthDoc["redirect_uri"],
                }


    @classmethod
    def parse(cls, api, json):
        oauth2 = cls(api)
        for k, v in json.items():
            setattr(oauth2, k, v)
        
        return oauth2


class User(Model):

    @classmethod
    def _gen_model(cls, api, doc):
        modelDict = {
            "id":doc["_id"],
            "name":doc["name"],
            "email": doc["email"],
            "pw_hash": doc["pw_hash"],
            "locale": doc["locale"],
            "timezone": doc["timezone"],
            "reg_date": doc["reg_date"],
            "providers": doc["providers"],
            #"session_id": doc["session_id"],
            "invitates": [],

        }
        invitates = mongo.db.invitates.find({"author_id":doc["_id"]})
        for i in invitates:
            modelDict["invitates"].append({
                "code":i["code"],
                "author_id":i["author_id"],
                "used":i["used"],
                "create_time":i["create_time"],
                "use_time":i["use_time"],
            })

        
        return modelDict


    @classmethod
    def get_user_profile(cls, api, parameters):
        """
        authenticate user via id or email, and password.
        """
        #print "get_user_profile parameters:", parameters
        login = parameters.get('login', None)
        id = parameters.get('id', None)
        email = parameters.get('email', None)
        provider = parameters.get('provider', None)
        user_id_provider = parameters.get('user_id_provider', None)
        userDoc = None

        if provider and user_id_provider:
            userDoc = mongo.db.users.find_one({"providers": 
                { "$elemMatch": {"provider":provider, "id":user_id_provider} } 
                })
            #print "3:", userDoc
        elif login!=None:
            userDoc = mongo.db.users.find_one({"$or": [{"_id":login}, {"email":login}]})
        elif id != None or email != None:
            userDoc = mongo.db.users.find_one({"$or": [{"_id":id}, {"email":email}]})
        else:
            raise DbapiError("Must specify 'id' or 'email' or 'login' to authenticate user!")

        if not userDoc:
            api.error = "No such user!"
            api.success = False
            return {}

        #print "1:", userDoc

        return cls._gen_model(api, userDoc)


    @classmethod
    def update_user_profile(cls, api, parameters):
        userid = parameters.get('user_id', None)
        username = parameters.get('user_name', userid)
        upsert = parameters.get('upsert', None)
        provider = parameters.get('provider', None)
        user_id_provider = parameters.get('user_id_provider', None)
        if not upsert:
            upsert=True
        else:
            upsert = True if upsert=='True' else False

        if userid==None and not upsert:
            raise DbapiError("Must specify 'user_id' to update user profile!")
        else:
            if provider and user_id_provider:
                userid = str(ObjectId())

        userDoc = mongo.db.users.find_one({"_id":userid})
        if userDoc==None and not upsert:
            raise DbapiError("user %s not found!" % userid)

        reg_date = int(time.time())
        if userDoc==None:
            userDoc = {}
            userDoc["_id"] = userid
            userDoc["invitation_code"] = None
            userDoc["pw_hash"] = "@$%$$%@#$%@#$%@#$%" # can be anything 
            userDoc["email"] = None
            userDoc["name"] = username
            userDoc["locale"] = 'zh_CN'
            userDoc["timezone"] = 'Asia/Shanghai'
            userDoc["introduction"] = ''
            userDoc["reg_date"] = reg_date
            userDoc["providers"] = []
            userDoc["copyrights"] = "user"

        name = parameters.get('name', None)
        if name!=None:
            userDoc["name"] = name
        email = parameters.get('email', None)
        if email != None:
            userDoc["email"] = email
        new_pw_hash = parameters.get('new_pw_hash', None)
        if new_pw_hash != None:
            userDoc["pw_hash"] = new_pw_hash
        invitation_code = parameters.get('invitation_code', None)
        if invitation_code != None and invitation_code!="OPENINVITATION":
            userDoc["invitation_code"] = invitation_code
            # disable used invitation code
            mongo.db.invitates.update({"code":invitation_code, "used":'False'}, 
                                  { '$set':{"used":name, "use_time":reg_date} }, 
                                  multi=True, upsert= False, safe = True);
        locale = parameters.get('locale', None)
        if locale:
            userDoc["locale"] = locale
        timezone = parameters.get('timezone', None)
        if timezone:
            userDoc["timezone"] = timezone
        introduction = parameters.get('introduction', None)
        if introduction:
            userDoc["introduction"] = introduction
        #session_id = parameters.get('session_id', None)
        #if session_id != None:
        #    userDoc["session_id"] = session_id
        
        #print "2:", userDoc

        mongo.db.users.update({"_id":userid}, userDoc, upsert=True)


        return cls._gen_model(api, userDoc)

    @classmethod
    def _pick_sina_weibo_profile(cls, provider, profile):
        """
        we will pick following information from the :profile: parameter:
        'id','access_token','expires_in','screen_name','avatar_large',
        'profile_image_url','syncd_status_idstr','last_sync_time',
        'last_status_idstr','last_status_text'
        """
        #print profile
        profile = json_decode(profile)
        return {
            'id':profile['idstr'],#user id for this provider
            'provider': provider,
            'screen_name' : profile['screen_name'],
            'avatar_large' : profile['avatar_large'],
            'profile_image_url' : profile['profile_image_url'],
            #'syncd_status_idstr' : profile['syncd_status_idstr'],
            #'last_sync_time' : profile['last_sync_time'],
            'last_status_idstr' : profile['status']['idstr'],
            'last_status_text' : profile['status']['text'],
            'last_auth_time': int(time.time()),#time in long integer format
        }


    @classmethod
    def remove_provider(cls, api, parameters):
        """
        remove a specified provider
        """
        print "remove_provider: parameters:", parameters
        userid = parameters.get('user_id', None)
        provider = parameters.get('provider', None)
        userid_provider = parameters.get('user_id_provider', None)

        if not userid or not provider or not userid_provider:
            raise DbapiError("remove provider insufficient parameter")

        userDoc = mongo.db.users.find_and_modify({"_id":userid},
            { '$pull':{"providers":{"id":userid_provider, "provider": provider}} },
            new = True
        )
        return cls._gen_model(api, userDoc)



    @classmethod
    def upsert_provider(cls, api, parameters):
        """
        update or insert a provider

        To support different providers, we only store specified 
        attributes.

        last_status_idstr是从user信息获取
        next_cursor是从user_timeline获取
        """
        #print "upsert_provider: parameters:", parameters
        userDoc = None
        userid = parameters.get('user_id', None)
        provider = parameters.get('provider', None)
        profile = parameters.get('their_profile', None)
        access_token = parameters.get('access_token', None)
        expires_in = parameters.get('expires_in', None)
        userid_provider = parameters.get('user_id_provider', None)
        next_count = parameters.get('next_count', None)
        next_cursor = parameters.get('next_cursor', None)

        if (userid==None or provider==None
            ):
            raise DbapiError("upsert_provider Fail: userid and provider must not be None")

        userDoc = mongo.db.users.find_one({"_id":userid})
        if userDoc==None:
            raise DbapiError("user %s not found!" % userid)

        # update only next count/cursor
        if next_count or next_cursor:
            if not userid_provider:
                raise DbapiError("user id for provider must provided for next count/cursor!")

            if not (next_count and next_cursor):
                raise DbapiError("both count/cursor must provided for next count/cursor!")

            r = mongo.db.users.update({"_id":userid,
                "providers":{
                    "$elemMatch":{"id":userid_provider, "provider": provider }
                    }
                },
                {'$set':{
                    'providers.$.next_count': int(next_count), 
                    'providers.$.next_cursor': next_cursor, 
                    }
                }, safe=True, upsert=False)
            #print r
            #like {u'updatedExisting': True, u'connectionId': 85, u'ok': 1.0, u'err': None, u'n': 1}
            userDoc = mongo.db.users.find_one({"_id":userid,
                "providers":{
                    "$elemMatch":{"id":userid_provider, "provider": provider }
                    }
                })
            return cls._gen_model(api, userDoc)

        #update entire provider
        if not profile:
            raise DbapiError("their_profile must provided to update provider!")

        if not access_token or not expires_in:
            raise DbapiError("access_token and expires_in must provided to update provider!")

        #refine the profile
        profile = cls._pick_sina_weibo_profile(provider, profile)
        if userid_provider:
            #it is provided
            if profile["id"] != usreid_provider:
                raise DbapiError("user id for the provider is mismatched!")
        # now the two are same
        userid_provider = profile["id"]

        profile["access_token"] = access_token
        profile["expires_in"] = int(expires_in)


        #refer: SO-10277174
        userDoc = mongo.db.users.find_one({"_id":userid,
            "providers":{
                "$elemMatch":{"id":userid_provider, "provider": provider }
                }
            })

        #insert new or update
        if userDoc is None:
            r = mongo.db.users.update({"_id":userid},
                {'$push':{
                    'providers': profile
                    },
                 '$set':{
                    'name': profile["screen_name"]
                    },
                }, safe=True, upsert=False)
            #print r
        else:
            r = mongo.db.users.update({"_id":userid,
                "providers":{
                    "$elemMatch":{"id":profile["id"], "provider": provider }
                    }
                },
                {'$set':{
                    'providers.$': profile
                    }
                }, safe=True, upsert=False)
            #print r

        userDoc = mongo.db.users.find_one({"_id":userid})
        return cls._gen_model(api, userDoc)


    @classmethod
    def parse(cls, api, json):
        user = cls(api)
        for k, v in json.items():
            setattr(user, k, v)
        
        return user


class Counter(Model):


    @classmethod
    def count_notes(cls, api, parameters):
        """handler method for count notes"""
        #print "note counter: parameters:", parameters

        spec = {}
        authorId = parameters.get('author_id', "")
        if authorId=="":
            raise DbapiError("Must specify 'author_id' to add_note!")
        spec["author_id"] = authorId

        shared_only = parameters.get('shared_only', None)
        if shared_only == "True":
            spec["shared"] = True

        hostId = parameters.get('host_id', None)
        spec["host_id"] = hostId

        threadId = parameters.get('thread_id', "")
        if threadId != "":
            spec["threads"] = {"$elemMatch":{"id":threadId }}

        return mongo.db.messages.find(spec).count()
        

    @classmethod
    def parse(cls, api, json):
        return json


class ModelFactory(object):
    """
    Used by parsers for creating instances
    of models. You may subclass this factory
    to add your own extended models.
    """

    note = Note
    counter = Counter
    thread = Thread
    paper = Paper
    list = List
    user = User

    json = JSONModel
    ids = IDModel

