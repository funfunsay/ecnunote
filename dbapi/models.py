# -*- coding: utf-8 -*-
# Fun2say
# Copyright 2012 Brent Jiang
# See LICENSE for details.

# !!! IMPORTANT NOTICE !!!
# Must use dict.get(<field-name>, <default-value>) instead of 
# dict[<field-name>] when fetching data from handler.parameters
# 
# 2012-04-19
# - add html escape/unescape 

import pymongo
from pymongo.objectid import ObjectId
import time
import sys
from fun2say.error import Fun2sayError
from fun2say.utils import parse_datetime, parse_html_value, parse_a_href, \
        parse_search_datetime, unescape_html
from fun2say.utils.escape import (xhtml_escape, 
    xhtml_unescape, json_decode, json_encode)

## test for not unescape
def source_unescape(str):
    return str
def source_escape(str):
    return str

class ResultSet(list):
    """A list like object that holds results from a Flask-Fun2say API query."""


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
            raise Fun2sayError("Must specify 'author_id' to add_note!")

        source = parameters.get('source', "")
        if source=="":
            raise Fun2sayError("Must specify 'source' to add_note!")

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
            paperDoc = api.db.papers.find_one({"_id":ObjectId(paperId)})

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

        ids = api.db.messages.insert(doc)
        if paperId!="":
            paperDoc = api.db.papers.find_one({"_id":ObjectId(paperId)})
            paperDoc["notes"].append({"id":str(ids), "order":len(paperDoc["notes"])+1})
            paperDoc["modified_date"] = pubDate
            api.db.papers.save(paperDoc)

        doc["_id"] = ids

        return cls._gen_model(doc)

    @classmethod
    def update(cls, api, parameters):
        """handler method for update_note"""
        #print "note update: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise Fun2sayError("Note ID must provided for update!")

        doc = api.db.messages.find_one({"_id":ObjectId(noteId)})
        if doc == None:
            raise Fun2sayError("Cannot find the note to be updated!")

        shared = parameters.get('shared', None)
        #print "shared:", shared
        if shared!=None:
            doc["shared"] = True if shared=="True" else False
        
        doc['modified_date'] = int(time.time())

        source = parameters.get("source", "")
        if source!="":
            doc["text"] = source_escape(source)
        doc["host_id"] = parameters.get("host_id", doc["host_id"])

        status = api.db.messages.update({"_id":ObjectId(noteId)},
                                        doc, upsert=False, safe=True)

        return cls._gen_model(doc)


    @classmethod
    def attach_note_to_paper(cls, api, paperid, noteid):
        #print "attach_note_to_paper ", noteid
        paperDoc = api.db.papers.find_one({"_id": ObjectId(paperid)})
        if paperDoc == None:
            #raise Fun2sayError("Cannot find the paper to be updated!")
            #don't raise error: maybe ...
            return

        #print paperDoc
        for order in paperDoc['notes']:
            if order['id'] == noteid:
                #print "return =="
                return order['order']
        
        order = len(paperDoc['notes'])+1
        paperDoc["modified_date"] = int(time.time())
        api.db.papers.update({"_id":ObjectId(paperid)},
            paperDoc, upsert=False, safe=True)
        api.db.papers.update({"_id":ObjectId(paperid)},
            {'$push':{'notes': {'id':noteid, 'order':order} }})

        return order


    @classmethod
    def detach_note_from_paper(cls, api, paperid, noteid):
        #print "detach_note_from_paper ", noteid
        paperDoc = api.db.papers.find_one({"_id": ObjectId(paperid)})
        if paperDoc == None:
            #raise Fun2sayError("Cannot find the paper to be updated!")
            # don't raise error: maybe the paper has been deleted!
            return

        notePos = 0
        for note in paperDoc['notes']:
            if note['id']==noteid:
                notePos = note['order']

        for note in paperDoc['notes']:
            if note['order']>notePos:
                note['order'] -= 1
                api.db.messages.update(
                    {'_id':ObjectId(note['id']), "papers":{"$elemMatch":{"id":paperid }}},
                    {'$inc':{"papers.$.order":-1}}
                    )

        #paperDoc['notes'][:] = [d for d in paperDoc['notes'] if d.get('id') != noteid]
        # update orders first
        paperDoc["modified_date"] = int(time.time())
        api.db.papers.update({"_id":ObjectId(paperid)},
            paperDoc, upsert=False, safe=True)
        # then pull
        api.db.papers.update({"_id":ObjectId(paperid)},
            {'$pull':{"notes": {"id":noteid }}})


    @classmethod
    def set_papers(cls, api, parameters):
        """handler method for set_papers"""
        #print "note set_papers: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise Fun2sayError("set note papers: note id must provide!")
        doc = api.db.messages.find_one({"_id":ObjectId(noteId)})
        if doc == None:
            raise Fun2sayError("Cannot find the note to be updated!")

        # must do detach before attach!
        oldPapers = api.db.papers.find({"notes": {"$elemMatch":{"id":noteId }}})
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

        status = api.db.messages.update({"_id":ObjectId(noteId)},
                                        doc, upsert=False, safe=True)

        return cls._gen_model(doc)


    @classmethod
    def set_threads(cls, api, parameters):
        """handler method for set_threads"""
        #print "note set_threads: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise Fun2sayError("set note threads: note id must provide!")

        doc = api.db.messages.find_one({"_id":ObjectId(noteId)})
        if doc == None:
            raise Fun2sayError("Cannot find the note to be updated!")

        doc["threads"] = []
        for thread in parameters["threads"].split('&'):
            doc["threads"].append({'id':thread})

        status = api.db.messages.update({"_id":ObjectId(noteId)},
            doc, upsert=False, safe=True)

        return cls._gen_model(doc)


    @classmethod
    def remove(cls, api, parameters):
        """handler method for delete_note"""
        #print "note remove: parameters:", parameters
        noteId = parameters.get("id", "")
        if noteId=="":
            raise Fun2sayError("remove note: note id must provide!")

        noteDoc = api.db.messages.find_one({"_id":ObjectId(noteId)})
        if noteDoc == None:
            raise Fun2sayError("Cannot find the note to be removed!")
 
        ##remove note from all papers
        for paper in noteDoc["papers"]:
            cls.detach_note_from_paper(api, paper["id"], noteId)
       
        status = api.db.messages.remove({"_id":ObjectId(noteId)})

        return cls._gen_model(noteDoc)


    @classmethod
    def take_in_note(cls, api, parameters):
        """
        Update the content when take in more times.
        """
        noteId = parameters.get("id", "")
        if noteId=="":
            raise Fun2sayError("take in ntoe: note id must provided!")

        userId = parameters.get("user_id", "")
        if userId=="":
            raise Fun2sayError("user id must provided!")

        noteDoc = api.db.messages.find_one({"take_in_id":noteId, "author_id":userId})
        if noteDoc == None:
            noteDoc = api.db.messages.find_one({"_id":ObjectId(noteId)})
            if noteDoc == None:
                ## @todo: how if the user take in just when the author delete it??
                raise Fun2sayError("Cannot find the note to be taken in!")

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
                api.db.messages.save(noteDoc)
        #@todo: if user modified taken-in note, how?
        # so wont support it now! maybe later!
        #@fixed: now take-in notes are not allowed to be modified.
        # so just let user update the note when take-in again
        else:
            ## has taken, so update the content!
            updatedNoteDoc = api.db.messages.find_one({"_id":ObjectId(noteId)})
            if userId != str(updatedNoteDoc["author_id"]):
                noteDoc["text"] = updatedNoteDoc["text"]
                noteDoc["modified_date"] = updatedNoteDoc["modified_date"]
                api.db.messages.save(noteDoc)

        return cls._gen_model(noteDoc)
    
    @classmethod
    def _query_one(cls, api, parameters, id):
        """handler method for query_note.
        Query database and generate a payload contains JSON objects.

        This function is a combination of database query and self.parse()
        """
        #print "note query: parameters:", parameters
        noteDoc = api.db.messages.find_one({"_id":ObjectId(id)})
        if noteDoc==None:
            raise Fun2sayError("Query one note failed on id %s"%(id))

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
        noteDocs = api.db.messages.find({"papers": {"$elemMatch":{"id":paperId}}})
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
                raise Fun2sayError("note query error: both paperId and threadId specified! ")
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
                noteDocs = api.db.messages.find(spec, 
                    sort=[(sort, direction)]).skip((page-1)*perPage).limit(perPage)
        else:
            lastDoc = api.db.messages.find_one({"_id":ObjectId(lastIds)})
            if lastDoc == None:
                raise Fun2sayError("note query: last ids invalid!")

            if sort=='papers.$.order':
                skip = 0
                for singleitem in lastDoc["papers"]:
                    if singleitem["id"] == paperId:
                        skip = int(singleitem["order"])
                        break
                noteDocs = cls._notes_in_paper_order(api, paperId, perPage, skip, shared_only, direction)
            else:
                spec[sort]= {"$lt" if direction==pymongo.DESCENDING else "$gt": lastDoc[sort]}
                noteDocs = api.db.messages.find(spec, 
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
            raise Fun2sayError("Author ID doesn't provided for add thread")
        name = parameters.get("name", "")
        if name=="":
            raise Fun2sayError("Thread name doesn't provided for add thread")
        shared = parameters.get("shared", False)

        threadDoc = api.db.threads.find_one({"author_id":authorId, "name":name})
        if threadDoc == None:
            threadDoc = {}
            threadDoc["author_id"] = authorId
            threadDoc["name"] = name
            threadDoc["shared"] = shared
            threadDoc["_id"] = ObjectId(api.db.threads.insert(threadDoc))
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
            raise Fun2sayError("Thread ID doesn't provided for update thread")
        name = parameters.get("name", "")
        shared = parameters.get("shared", None) #it's 'None'! not default 'False'

        threadDoc = api.db.threads.find_one({"_id":ObjectId(threadId)})
        if threadDoc == None:
            raise Fun2sayError("Thread with id %s doesn't exists" % threadId)

        if name!= "":
            threadDoc["name"] = name
        if shared!= None:
            threadDoc["shared"] = shared
        api.db.threads.update({"_id":ObjectId(threadId)}, 
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
            raise Fun2sayError("Thread ID doesn't provided for update thread")

        threadDoc = api.db.threads.find_one({"_id":ObjectId(threadId)})
        if threadDoc == None:
            raise Fun2sayError("Thread with id %s doesn't exists" % threadId)
        api.db.threads.remove({"_id":ObjectId(threadId)})
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
            raise Fun2sayError("Author ID doesn't provided for query threads")

        threadDocs = api.db.threads.find({"author_id":authorId})

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
            raise Fun2sayError("Author ID doesn't provided for add paper")
        name = parameters.get("name", "")
        if name=="":
            raise Fun2sayError("Paper name doesn't provided for add paper")
        shared = parameters.get("shared", None)
        shared = True if shared=="True" else False ## 'None' means "not share"
        curTime = int(time.time())

        paperDoc = api.db.papers.find_one({"author_id":authorId, "name":name})
        if paperDoc == None:
            paperDoc = {}
            paperDoc["author_id"] = authorId
            paperDoc["name"] = name
            paperDoc["shared"] = shared
            paperDoc["notes"] = []
            paperDoc["pub_date"] = curTime
            paperDoc["modified_date"] = curTime
            paperDoc["_id"] = ObjectId(api.db.papers.insert(paperDoc))
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
            raise Fun2sayError("Paper ID doesn't provided for update paper")
        name = parameters.get("name", "")
        shared = parameters.get("shared", None) #it's 'None'! not default 'False'
        shared = True if shared=="True" else False ## 'None' means "not share"

        paperDoc = api.db.papers.find_one({"_id":ObjectId(paperId)})
        if paperDoc == None:
            raise Fun2sayError("Paper with id %s doesn't exists" % paperId)

        curTime = int(time.time())

        if name!= "":
            paperDoc["name"] = name
        if shared!= None:
            paperDoc["shared"] = shared
            paperDoc["modified_date"] = curTime
        api.db.papers.update({"_id":ObjectId(paperId)}, 
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
            raise Fun2sayError("Paper ID doesn't provided for update paper")

        paperDoc = api.db.papers.find_one({"_id":ObjectId(paperId)})
        if paperDoc == None:
            raise Fun2sayError("Thread with id %s doesn't exists" % paperId)
        api.db.papers.remove({"_id":ObjectId(paperId)})
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

        paperDocs = api.db.papers.find(spec, sort=[("modified_date", pymongo.DESCENDING)]).limit(0)

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
            raise Fun2sayError("start_pos doesn't provided for query papers")
        startPos = int(startPos)
        stopPos = parameters.get('stop_pos', None)
        if stopPos==None:
            raise Fun2sayError("stop_pos doesn't provided for query papers")
        stopPos = int(stopPos)
        paperId = parameters.get('id', None)
        if paperId==None:
            raise Fun2sayError("paper id doesn't provided for query papers")
        authorId = parameters.get('author_id', None)
        if authorId==None:
            raise Fun2sayError("Author ID doesn't provided for query papers")

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

        paperDoc = api.db.papers.find_one({"_id":ObjectId(paperId),
             "author_id":authorId});
        if paperDoc==None:
            raise Fun2sayError("Cannot find paper to change order")

        #print paperDoc
        #re-order in db
        for note in paperDoc['notes']:
            if note['order']==startPos:
                note['order'] = stopPos
                api.db.messages.update(
                    {'_id':ObjectId(note['id']), "papers":{"$elemMatch":{"id":paperId }}}, 
                    {'$set':{"papers.$.order":stopPos}}
                    )
            elif note['order']>=min and note['order']<max:
                note['order']+=incValue
                api.db.messages.update(
                    {'_id':ObjectId(note['id']), "papers":{"$elemMatch":{"id":paperId }}},
                    {'$inc':{"papers.$.order":incValue}}
                    )

        paperDoc["modified_date"] = int(time.time())
        status = api.db.papers.update({'_id':paperDoc['_id']}, paperDoc, upsert= False, safe = True)
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
            raise Fun2sayError("Must specify 'provider' to get_key")
        oauthDoc = api.db.oauths.find_one({'provider':provider})
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
        invitates = api.db.invitates.find({"author_id":doc["_id"]})
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
            userDoc = api.db.users.find_one({"providers": 
                { "$elemMatch": {"provider":provider, "id":user_id_provider} } 
                })
            #print "3:", userDoc
        elif login!=None:
            userDoc = api.db.users.find_one({"$or": [{"_id":login}, {"email":login}]})
        elif id != None or email != None:
            userDoc = api.db.users.find_one({"$or": [{"_id":id}, {"email":email}]})
        else:
            raise Fun2sayError("Must specify 'id' or 'email' or 'login' to authenticate user!")

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
            raise Fun2sayError("Must specify 'user_id' to update user profile!")
        else:
            if provider and user_id_provider:
                userid = str(ObjectId())

        userDoc = api.db.users.find_one({"_id":userid})
        if userDoc==None and not upsert:
            raise Fun2sayError("user %s not found!" % userid)

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
            api.db.invitates.update({"code":invitation_code, "used":'False'}, 
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

        api.db.users.update({"_id":userid}, userDoc, upsert=True)


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
            raise Fun2sayError("remove provider insufficient parameter")

        userDoc = api.db.users.find_and_modify({"_id":userid},
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
            raise Fun2sayError("upsert_provider Fail: userid and provider must not be None")

        userDoc = api.db.users.find_one({"_id":userid})
        if userDoc==None:
            raise Fun2sayError("user %s not found!" % userid)

        # update only next count/cursor
        if next_count or next_cursor:
            if not userid_provider:
                raise Fun2sayError("user id for provider must provided for next count/cursor!")

            if not (next_count and next_cursor):
                raise Fun2sayError("both count/cursor must provided for next count/cursor!")

            r = api.db.users.update({"_id":userid,
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
            userDoc = api.db.users.find_one({"_id":userid,
                "providers":{
                    "$elemMatch":{"id":userid_provider, "provider": provider }
                    }
                })
            return cls._gen_model(api, userDoc)

        #update entire provider
        if not profile:
            raise Fun2sayError("their_profile must provided to update provider!")

        if not access_token or not expires_in:
            raise Fun2sayError("access_token and expires_in must provided to update provider!")

        #refine the profile
        profile = cls._pick_sina_weibo_profile(provider, profile)
        if userid_provider:
            #it is provided
            if profile["id"] != usreid_provider:
                raise Fun2sayError("user id for the provider is mismatched!")
        # now the two are same
        userid_provider = profile["id"]

        profile["access_token"] = access_token
        profile["expires_in"] = int(expires_in)


        #refer: SO-10277174
        userDoc = api.db.users.find_one({"_id":userid,
            "providers":{
                "$elemMatch":{"id":userid_provider, "provider": provider }
                }
            })

        #insert new or update
        if userDoc is None:
            r = api.db.users.update({"_id":userid},
                {'$push':{
                    'providers': profile
                    },
                 '$set':{
                    'name': profile["screen_name"]
                    },
                }, safe=True, upsert=False)
            #print r
        else:
            r = api.db.users.update({"_id":userid,
                "providers":{
                    "$elemMatch":{"id":profile["id"], "provider": provider }
                    }
                },
                {'$set':{
                    'providers.$': profile
                    }
                }, safe=True, upsert=False)
            #print r

        userDoc = api.db.users.find_one({"_id":userid})
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
            raise Fun2sayError("Must specify 'author_id' to add_note!")
        spec["author_id"] = authorId

        shared_only = parameters.get('shared_only', None)
        if shared_only == "True":
            spec["shared"] = True

        hostId = parameters.get('host_id', None)
        spec["host_id"] = hostId

        threadId = parameters.get('thread_id', "")
        if threadId != "":
            spec["threads"] = {"$elemMatch":{"id":threadId }}

        return api.db.messages.find(spec).count()
        

    @classmethod
    def parse(cls, api, json):
        return json


class Syncmtask(Model):
    """
    Sync Manager 

    在新浪微博API中，user_timeline的参数：
    since_id 	false 	int64 	若指定此参数，则返回ID比since_id大的微博（即比since_id时间晚的微博），默认为0。
    max_id 	false 	int64 	若指定此参数，则返回ID小于或等于max_id的微博，默认为0。 

    db.syncmtasks 集合之中有waiting、pending和finished三种类型
    - pending：新的任务
    - running：已经由sync-task开始处理的任务，正在等待结果
    - finished：任务已经完成
    """

    @classmethod
    def _gen_model(cls, taskDoc):
        return {
            "id":str(taskDoc["_id"]),
            "provider":taskDoc['provider'],
            'user_id':taskDoc['user_id'],
            'user_id_provider':taskDoc['user_id_provider'],
            'count': taskDoc['count'],
            'cursor':taskDoc['cursor'],#previous last for me to start $gt
            'next_count': taskDoc['count'],
            'my_last_syncd_idstr':taskDoc['my_last_syncd_idstr'], #my last for next task
            'pub_time':taskDoc['pub_time'],
            'finished_time':taskDoc['finished_time'],
            'state':taskDoc['state'],#pending, running, finished, canceled
        }

    @classmethod
    def get_sync_tasks(cls, api, parameters):
        """
        """
        spec = {}
        count = int(parameters.get('count', 25))
        user_id = parameters.get('user_id', None)
        user_id_provider = parameters.get('user_id_provider', None)
        state = parameters.get('state', None)

        if user_id:
            spec["user_id"] = user_id
        provider = parameters.get('provider', None)
        if provider:
            spec["provider"] = provider
        if user_id_provider:
            spec["user_id_provider"] = user_id_provider
        if state:
            spec["state"] = state

        taskDocs = api.db.syncmtasks.find(spec).limit(count)
        models = []
        for taskDoc in taskDocs:
            modelDict = cls._gen_model(taskDoc)
            models.append(modelDict)

        return tuple(models)

    @classmethod
    def add_sync_task(cls, api, parameters):
        """
        if cursor is None, then check whether the corresponding
        user-provider pair has been synced.

        新增加的任务状态为：pending
        """
        provider = parameters.get('provider', None)
        user_id = parameters.get('user_id', None)
        user_id_provider = parameters.get('user_id_provider', None)
        if provider==None or user_id==None or user_id_provider==None:
            raise Fun2sayError("add sync task information lose!")
        count = parameters.get('count', 25)

        cursor = parameters.get('cursor', None)
        if cursor is None:
            # not provide last id, judge
            pending_running = api.db.syncmtasks.find_one({'provider':provider,
                'user_id':user_id,
                'user_id_provider':user_id_provider,
                '$or': [{'state':'pending'}, {'state':'running'}],
            })

            if pending_running:
                # no need to add
                return cls._gen_model(pending_running)

            finished = api.db.syncmtasks.find_one({'provider':provider,
                'user_id':user_id,
                'user_id_provider':user_id_provider,
                'state':'finished',
            }, sort=[('finished_time', pymongo.DESCENDING)])

            if finished:
                cursor = finished['my_last_syncd_idstr']
                count = finished['next_count']
            else:
                # sina weibo uses '0' as the beginning of all status
                cursor = "0"
        else:
            existing = api.db.syncmtasks.find_one({'provider':provider,
                'user_id':user_id,
                'user_id_provider':user_id_provider,
                'cursor':cursor,
            })

            if existing:
                # already syncd, no need 
                return cls._gen_model(existing)

        pub_time = int(time.time())
        state = 'pending'

        ids = api.db.syncmtasks.insert({
            'provider': provider,
            'user_id':user_id,
            'user_id_provider':user_id_provider,
            'count': count,
            'cursor':cursor,
            'next_count':None,
            'next_cursor':None,
            'my_last_syncd_idstr':None,
            'state':'pending',
            'pub_time': pub_time,
            'finished_time':None,
        })

        return cls._gen_model(api.db.syncmtasks.find_one({"_id":ids}))


    @classmethod
    def start_sync_task(cls, api, parameters):
        print "start_sync_task parameters:", parameters
        provider = parameters.get('provider', None)
        user_id = parameters.get('user_id', None)
        user_id_provider = parameters.get('user_id_provider', None)
        if provider==None or user_id==None or user_id_provider==None:
            raise Fun2sayError("start sync task information lose!")
        api.db.syncmtasks.update({"user_id":user_id,
            "user_id_provider": user_id_provider,
            "provider":provider,
            "state": "pending",
            }, 
            {"$set": {"state": "running"}}
        )
        syncmtaskDoc = api.db.syncmtasks.find_one({"user_id":user_id,
            "user_id_provider": user_id_provider,
            "provider":provider,
            "state": "running"
        })
        return cls._gen_model(syncmtaskDoc)

    @classmethod
    def finish_sync_task(cls, api, parameters):
        print "finish_sync_task parameters:", parameters
        provider = parameters.get('provider', None)
        user_id = parameters.get('user_id', None)
        user_id_provider = parameters.get('user_id_provider', None)
        my_last_syncd_idstr = parameters.get('my_last_syncd_idstr', None)
        next_cursor = parameters.get('next_cursor', None)
        count = parameters.get('count', None)
        if provider==None or user_id==None or user_id_provider==None:
            raise Fun2sayError("add sync task information lose!")

        syncmtaskDoc = api.db.syncmtasks.find_one({"user_id":user_id,
            "user_id_provider": user_id_provider,
            "provider":provider,
            "state": "running"
        })
        if not syncmtaskDoc:
            raise Fun2sayError("no such task found for updating!")

        syncmtaskDoc["state"] = "finished"
        syncmtaskDoc["finished_time"] = int(time.time())
        if count:
            syncmtaskDoc["count"] = count
        if my_last_syncd_idstr:
            syncmtaskDoc["my_last_syncd_idstr"] = my_last_syncd_idstr
        else:
            # keep the old cursor
            syncmtaskDoc["my_last_syncd_idstr"] = syncmtaskDoc["cursor"]

        syncmtaskDoc["next_cursor"] = next_cursor
        if next_cursor=="0":
            syncmtaskDoc["next_count"] = 25
        else:
            syncmtaskDoc["next_count"] = syncmtaskDoc["count"] * 2

        #print syncmtaskDoc

        api.db.syncmtasks.save(syncmtaskDoc)

        #if has more, then start a new task
        if next_cursor!="0":
            # publish a new sync task for this provider-connection
            ids = api.db.syncmtasks.insert({
                'provider': provider,
                'user_id':user_id,
                'user_id_provider':user_id_provider,
                'count': syncmtaskDoc["next_count"],
                'cursor':syncmtaskDoc["my_last_syncd_idstr"],
                'next_count':None,
                'next_cursor':None,
                'my_last_syncd_idstr':None,
                'state':'pending',
                'pub_time': int(time.time()),
                'finished_time':None,
            })


        return cls._gen_model(syncmtaskDoc)

    @classmethod
    def parse(cls, api, json):
        syncmtask = cls(api)
        for k, v in json.items():
            setattr(syncmtask, k, v)
        
        return syncmtask

class Webac(Model):
    @classmethod
    def _gen_model(cls, api, parameters, doc):
        #print "_gen_model"
        timenow = int(time.time())
        # 虽然提示用户的时候说是耐心等待5秒钟，但是系统内容只等待4秒钟
        # 这样稍微提升一点用户使用感觉
        allowed = True if (timenow - int(doc["last_time"]))>=4 else False
        

        doc["allowed"] = allowed
        doc["last_time"] = timenow        
        api.db.webacs.save(doc)

        return {"allowed":allowed, 
                "ip": doc["ip"]
                }

    @classmethod
    def _gen_deny_model(cls):   
        #print "_gen_deny_model"     

        return {"allowed":False}

    @classmethod
    def _gen_allow_model(cls):        
        #print "_gen_allow_model"
        return {"allowed":True}

    @classmethod
    def check_request_interval(cls, api, parameters):
        #print "check_request_interval parameters:", parameters
        userip = parameters.get('ip', None)
        #print "userip"
        if not userip:
            return cls._gen_deny_model()

        acdoc = api.db.webacs.find_one({"ip": userip})
        if not acdoc:
            api.db.webacs.insert({"last_time":int(time.time()), 
                "ip": userip})
            return cls._gen_allow_model()

        return cls._gen_model(api, parameters, acdoc)

    @classmethod
    def parse(cls, api, json):
        webac = cls(api)
        for k, v in json.items():
            setattr(webac, k, v)
        
        return webac

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
    oauth2 = OAuth2
    user = User
    syncmtask = Syncmtask
    webac = Webac

    json = JSONModel
    ids = IDModel

