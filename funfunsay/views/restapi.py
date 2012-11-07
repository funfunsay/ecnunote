# -*- coding: utf-8 -*-
from flask import (Blueprint, render_template, current_app, request,
    flash, url_for, redirect, session, g, abort, jsonify,
    Markup)

notes = Blueprint('notes', __name__, url_prefix='/notes'
                       #,static_folder='/static'
                       )
threads = Blueprint('threads', __name__, url_prefix='/threads'
                       #,static_folder='/static'
                       )
users = Blueprint('users', __name__, url_prefix='/users'
                       #,static_folder='/static'
                       )
search = Blueprint('search', __name__, url_prefix='/search'
                       #,static_folder='/static'
                       )

@notes.route('/fetch.<format>', methods=['GET'])
def fetch(format):
    if format <> 'json':
        return jsonify(status=False, error="Unknown format.")

    authorid = request.args.get('authorid', '')
    number = request.args.get('number', 20)
    lastIds = request.args.get('last_id', "")
    threadid = request.args.get('threadid', '')
    #paperid = request.args.get('paperid', '')
    #tags = request.args.get('tags', '')
    sort = request.args.get('sort', '')
    direction = request.args.get('direction', '')
    #clear = request.args.get('clear', 'false')
    #criteria = request.args.get('criteria', '')
    sharedonly = True if request.args.get('sharedonly', 'false')=='true' else False
    #print "clear:", clear

    loadScript = True if lastIds=="" else False

    #print "number:", number, ", lastIds:", lastIds, ", threadid:", threadid, ", paperid:", paperid, ", tags:", tags
    notes = current_app.dbapi.user_timeline(author_id=authorid,
        shared_only=sharedonly, lastIds=lastIds, per_page=number,
        thread_id=threadid, 
        sort=sort, direction=direction)
    #print 'notes:', notes
    #for n in notes:
    #    print n.__dict__
    notes[:] = [x.__dict__ for x in notes]

    if len(notes)==0:
        #print "no more!"
        return jsonify(status=False, noMore=True)

    return jsonify(status=True, 
        notes=notes
        )
