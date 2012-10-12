"""
module version
"""
import time

# For import *
__all__ = ['init_global_versions', 'is_version_controled', 'get_head_version', 
           'get_new_version']

_global_version_controlled_collections = []

def new_global_version_document(collection_dict):
    return {"name": collection_dict["name"], #name of collection to be version controlled
            "field": collection_dict["field"],
            "version": 0,
            "userid": "__flask-vpymongo" #first document is created by the extension
            }


def new_global_version_log_document(name, version, message):
    """@faq: a problem faced is whether we need add an extra parameter
             "userid" to differentiate versions for different user
    """
    return {"name": name, # collection name
            "version": version,
            "time": int(time.time()),
            "userid": "__flask-vpymongo"
            }


def init_global_versions(db, collection_dict):
    if collection_dict['name']=='_global_versions':
        return 
    doc = db._global_versions.find_one({"name":collection_dict['name'], "field":collection_dict['field']})
    if doc==None:
        doc = new_global_version_document(collection_dict)
        db._global_versions.insert(doc)

    global _global_version_controlled_collections
    _global_version_controlled_collections.append(collection_dict['name'])


def is_version_controled(db, collection_name):
    """Judge whether there is an item in _global_version Collection"""
    # @faq: see night-3rd: 8.3.1.1	PyMongoV.Errors.AutoReconnect
    if collection_name=='_global_versions':
        return False
    #doc = db._global_versions.find_one({"name":collection_name})
    #return False if doc==None else True
    return True if collection_name in _global_version_controlled_collections else False


def get_head_version(db, collection_name):
    """return head version"""
    doc = db._global_versions.find_one({"name":collection_name}, 
                                       sort=[("version",pymongo.DESCENDING)])
    if doc==None:
        return -1

    return doc["version"]


def get_new_version(db, collection_name):
    """Increase and return the next version of this Collection"""
    doc = db._global_versions.find_one({"name":collection_name}, 
                                       sort=[("version",pymongo.DESCENDING)])
    if doc==None:
        return 0

    doc["version"] = int(doc["version"])+1
    db._global_versions.insert(doc)
    return doc["version"]
