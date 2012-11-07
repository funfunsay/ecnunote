# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime
import time

from flask import (Blueprint, render_template, current_app, request,
    flash, url_for, redirect, session, g, abort, jsonify,
    Markup)
from jinja2 import TemplateNotFound
from werkzeug import check_password_hash, generate_password_hash
from flask.ext.babel import gettext as _
from flask.ext.login import (login_required, login_user, current_user,
                            logout_user, confirm_login, fresh_login_required,
                            login_fresh)
from funfunsay.forms import (SignupForm, LoginForm, RecoverPasswordForm,
                         ChangePasswordForm, ReauthForm, UProfileForm)

from funfunsay.models import User
from funfunsay.extensions import cache
from funfunsay.views.pagination import Pagination
import markdown2


funnote = Blueprint('funnote', __name__, url_prefix='/n'
                       #,static_folder='/static'
                       )

@funnote.route('/', defaults={'page':1})
@funnote.route('/page/<int:page>')
@login_required
def index(page):
    """
    Index for FunFunSay Note.

    if you want to display notes of a paper, use 'paper' router.
    """
    # activethreadid is the id of thread
    activethreadid = request.args.get('activethreadid', "")
    activepaperid = request.args.get('activepaperid', "")

    messageCount = current_app.dbapi.count_notes(author_id=current_user.id,
        shared_only=False, host_id=None, thread_id=activethreadid)

    messages = current_app.dbapi.user_timeline(author_id=current_user.id,
        shared_only=False, page=page, thread_id=activethreadid)

    threads = current_app.dbapi.note_threads(author_id=current_user.id)
    papers = current_app.dbapi.get_papers(author_id=current_user.id)

    pagination = Pagination(page, 20, messageCount)

    #print create
    return render_template('funnote/funnote.html',
        notes=messages, 
        pagination=pagination, 
        threads=threads, 
        papers=papers,
        activethreadid=activethreadid,
        activepaperid=activepaperid,
        activetags='')


@funnote.route('/fast')
@login_required
def fastnote():

    threads = current_app.dbapi.note_threads(author_id=current_user.id)
    papers = current_app.dbapi.get_papers(author_id=current_user.id)
    return render_template('funnote/fastnote.html',
        threads=threads, 
        papers=papers
        )

@funnote.route('/funmark')
def funmark():
    login_form = signup_form = None
    if not current_user.is_authenticated():
        login_form= LoginForm(next=request.args.get('next'))
        signup_form = SignupForm(nex=request.args.get('next'))

    return render_template('md2img.html', 
        login_form=login_form,signup_form=signup_form)


@funnote.route('/paper')
@login_required
def paper():
    """
    Paper for FunFunSay Note.

    if you want to display notes of a thread, use 'index' router.
    """
    # activpaperid is the id of paper
    activepaperid = request.args.get('activepaperid', '')

    messages = current_app.dbapi.user_timeline(shared_only=False, 
        paper_id=activepaperid, sort='order_in_paper', per_page = 99999,
        direction='ascending')

    threads = current_app.dbapi.note_threads(author_id=current_user.id)
    userpapers = current_app.dbapi.get_papers(author_id=current_user.id)
    currentpaper = current_app.dbapi.get_papers(paper_id=activepaperid)[0]

    #print create
    return render_template('funnote/paper.html',
        notes=messages, 
        threads=threads, 
        papers=userpapers,
        activepaperid=activepaperid,
        activetags='',
        activethreadid='',
        paper=currentpaper)


@funnote.route('/message_page/<messageid>')
@login_required
def message_page(messageid):
    #print messageid

    threads = current_app.dbapi.note_threads(author_id=current_user.id)
    papers = current_app.dbapi.get_papers(author_id=current_user.id)

    return render_template('funnote/message.html', 
        message=current_app.dbapi.get_one_note(id=messageid), 
        comments=current_app.dbapi.user_timeline(
            host_id=messageid,shared_only=True),
        threads=threads,
        papers=papers,
        activepaperid='',
        activetags='',
        activethreadid=''
        )


@funnote.route('/save_message', methods=['POST'])
@login_required
def save_message():
    messageid = request.form['messageid']
    source = request.form['source']
    activethreadid = request.form['activethreadid']
    activepaperid = request.form['activepaperid']
    newmessageid=""
    notes=""

    if source and source <> '':
        if messageid is None or messageid.strip()== '':
            ## add new message
            newmessage = current_app.dbapi.add_note(
                author_id=current_user.id, source=source,
                thread_id=activethreadid, 
                paper_id=activepaperid)
            newmessageid = newmessage.id
            ##print "newmessage:", newmessage
            notes=render_template(
                'funnote/itemwidget.html',
                notes = [newmessage],
                loadScript = False,
                expanded = True
                )
            ##print "notes:", notes
        else:
            current_app.dbapi.update_note(
                id=messageid, source=source)

    #return redirect(url_for('funnote.index', 
    #    activethreadid=activethreadid, newmessageid=newmessageid))
    if newmessageid!="":
        if activepaperid!='':
            return jsonify(redirect=url_for('funnote.paper',
                activethreadid=activethreadid, 
                activepaperid=activepaperid), 
                notes=notes,
				messageid=newmessageid)
        return jsonify(redirect=url_for('funnote.index',
            activethreadid=activethreadid, 
            activepaperid=activepaperid),
            notes=notes,
			messageid=newmessageid)

    return jsonify(redirect="", notes=notes,
		messageid=messageid)


@funnote.route('/delete_message', methods=['post'])
@login_required
def delete_message():
    activethreadid = request.args.get('activethreadid', '')
    activepaperid = request.args.get('activepaperid', '')
    current_app.dbapi.delete_note(request.form['messageid'])
    if activepaperid!= '':
        return jsonify(redirect = url_for('funnote.paper', 
            activethreadid=activethreadid,
            activetags='',
            activepaperid=activepaperid))
    return jsonify(redirect = url_for('funnote.index', 
        activethreadid=activethreadid,
        activetags='',
        activepaperid=activepaperid))


@funnote.route('/save_comment', methods=['POST'])
@login_required
def save_comment():
    messageid = request.form['messageid']
    commentid = request.form['commentid']
    text = request.form['comment']
    activethreadid = request.args.get('activethreadid', '')

    ## comment default shared

    if text and text <> '':
        if commentid is None or commentid.strip()== '':
            current_app.dbapi.add_note(host_id=messageid, 
                author_id=current_user.id, source=text, 
                shared=True ## comment default shared
                )
        else:
            current_app.dbapi.update_note(id=commentid, source=text)

    return redirect(url_for('funnote.message_page', 
        messageid=messageid, 
        activethreadid=activethreadid))


@funnote.route('/delete_comment', methods=['post'])
@login_required
def delete_comment():
    commentid = request.form['commentid']
    note = current_app.dbapi.delete_note(id=commentid)
    return jsonify(redirect = url_for('funnote.message_page', 
        messageid=note.host_id))


@funnote.route('/add_thread', methods=['post'])
@login_required
def add_thread():
    activethreadid = request.args.get('activethreadid', '')
    activepaperid = request.args.get('activepaperid', '')
    name = request.form['name'].strip()
    if name=="":
        return jsonify(status=False)
    #print "name = %s, activethreadid=%s" %(name, activethreadid)
    thread = current_app.dbapi.add_thread(author_id=current_user.id, name=name)
    if not current_app.dbapi.success:
        #print current_app.dbapi.error
        return jsonify(status=False)
    #return jsonify(threadid=thread.id, threadname=thread.name, threadshared=thread.shared)
    return jsonify(status=True, 
        activethreadid=activethreadid, 
        activepaperid=activepaperid,
        html=render_template('funnote/threadli.html', thread=thread))


@funnote.route('/rename_thread', methods=['post'])
@login_required
def rename_thread():
    threadid = request.form['threadid']
    name = request.form['name']
    current_app.dbapi.update_thread(id=threadid, name=name)
    return jsonify(status=True)


@funnote.route('/_set_threads', methods=['post'])
@login_required
def set_threads():
    messageid = request.form['messageid']
    activepaperid = request.form['activepaperid']
    activethreadid = request.form['activethreadid']
    #print messageid
    threads = request.form['threads']
    current_app.dbapi.set_threads(id=messageid, threads=threads)
    if activethreadid != '' and threads.find(activethreadid)==-1:
        #doesn't belong to this thread anymore
        return jsonify(status=True,
            redirect=url_for('funnote.index', activethreadid=activethreadid),
            belongto=False)
    return jsonify(status=True,
        redirect="",
        belongto=True)


@funnote.route('/_modal_threads', methods=['get'])
@login_required
def modal_threads():
    #messageid = request.form['messageid']
    messageid = request.args.get('messageid')
    #print messageid
    message=current_app.dbapi.get_one_note(id=messageid)
    #print message.threads
    threads = current_app.dbapi.note_threads(author_id=current_user.id)

    return jsonify(status=True, 
        html=render_template('funnote/modal_threads.html', 
            message=message, threads=threads))

@funnote.route('/add_paper', methods=['post'])
@login_required
def add_paper():
    activepaperid = request.args.get('activepaperid', '')
    activethreadid = request.args.get('activethreadid', '')
    name = request.form['name'].strip()
    if name=="":
        ## @faq: can it return nothing when name==""?
        return jsonify(status=False)
    #print "name = %s, activepaperid=%s" %(name, activepaperid)
    paper = current_app.dbapi.add_paper(author_id=current_user.id, name=name)
    if not current_app.dbapi.success:
        #print current_app.dbapi.error
        return jsonify(status=False)
    #return jsonify(paperid=paper.id, papername=paper.name, papershared=paper.shared)
    return jsonify(status=True, 
        activepaperid=activepaperid,
        activethreadid=activethreadid,
        html=render_template('funnote/paperli.html', paper=paper))


@funnote.route('/rename_paper', methods=['post'])
@login_required
def rename_paper():
    paperid = request.form['paperid']
    name = request.form['name']
    current_app.dbapi.update_paper(id=paperid, name=name)
    return jsonify(status=True)


@funnote.route('/delete_paper', methods=['post'])
@login_required
def delete_paper():
    paperid = request.form['paperid']
    current_app.dbapi.delete_paper(id=paperid)
    return jsonify(redirect=url_for('funnote.index'))


@funnote.route('/delete_thread', methods=['post'])
@login_required
def delete_thread():
    threadid = request.form['threadid']
    current_app.dbapi.delete_thread(id=threadid)
    return jsonify(redirect=url_for('funnote.index'))


@funnote.route('/_set_papers', methods=['post'])
@login_required
def set_papers():
    messageid = request.form['messageid']
    activepaperid = request.form['activepaperid']
    activethreadid = request.form['activethreadid']
    #print messageid
    papers = request.form['papers']
    current_app.dbapi.set_papers(id=messageid, papers=papers)
    #print "activepaperid:", activepaperid
    #print "papers:", papers
    if activepaperid != '' and papers.find(activepaperid)==-1:
        # not belong to this paper anymore
        return jsonify(status=True,
            redirect=url_for('funnote.paper', activepaperid=activepaperid),
            belongto=False # not
            )
    return jsonify(status=True, belongto=True,
        redirect="")


@funnote.route('/_modal_papers', methods=['get'])
@login_required
def modal_papers():
    #messageid = request.form['messageid']
    messageid = request.args.get('messageid')
    #print messageid
    message=current_app.dbapi.get_one_note(id=messageid)
    #print message.papers
    papers = current_app.dbapi.get_papers(author_id=current_user.id)

    return jsonify(status=True, 
        html=render_template('funnote/modal_papers.html', 
            message=message, papers=papers))


@funnote.route('/change_order', methods=['POST'])
@login_required
def change_order():
    current_app.dbapi.change_order(id=request.form['id'], 
        start_pos=request.form['start_pos'], 
        stop_pos=request.form['stop_pos'],
        author_id=current_user.id)

    return jsonify(result=True)


@funnote.route('/shared_paper')
def shared_paper():
    paperId = request.args.get('id')
    messages = current_app.dbapi.user_timeline(shared_only=True, paper_id=paperId,
        sort='order_in_paper', direction='ascending')
    papers = current_app.dbapi.get_papers(paper_id=paperId)
    #print papers[0]
    return render_template('funnote/shared_paper.html', paper=papers[0], messages=messages)


@funnote.route('/share_note_switch', methods=['POST'])
def share_note_switch():
    noteId = request.form['id']
    shared = True if request.form['shared']=="true" else False
    note = current_app.dbapi.update_note(shared=shared, id=noteId)
    return jsonify(status = True if note.shared==shared else False)


@funnote.route('/share_paper_switch', methods=['POST'])
def share_paper_switch():
    paperId = request.form['id']
    shared = True if request.form['shared']=="true" else False
    paper = current_app.dbapi.update_paper(shared=shared, id=paperId)
    return jsonify(status = True if paper.shared==shared else False)


@funnote.route('/take_in_note/<id>', methods=['POST', 'GET'])
@login_required
def take_in_note(id):
    #print id, ",", current_user.is_authenticated()
    note = current_app.dbapi.take_in_note(id=id, user_id=current_user.id)
    status=True if note.author_id==current_user.id else False
    #flash("Note %s taked in." % note.id)
    return jsonify(status=status)

#杩欎釜瑙嗗浘澶勭悊鍣ㄦ病鏈変娇鐢ㄣ€傚洜涓哄叏閮ㄥ彲浠ラ€氳繃JS浠ｇ爜鍦–lient绔疄鐜帮紝
#杩欐牱鍙互闄嶄綆鏈嶅姟鍣ㄧ鐨勮繍绠楄礋鎷呫€?
@funnote.route('/_get_markdown', methods=['GET'])
def get_markdown():
    noteid = request.args.get('noteid', None)
    if not noteid:
        return jsonify(status=False)

    note = current_app.dbapi.get_one_note(id=noteid)
    return jsonify(status=True,
        content=markdown2.markdown(note.source) )

@funnote.route('/_get_original', methods=['GET'])
def get_original():
    noteid = request.args.get('noteid', None)
    if not noteid:
        return jsonify(status=False)

    note = current_app.dbapi.get_one_note(id=noteid)
    return jsonify(status=True,
        content=note.source )


@funnote.route('/_fetch_notes', methods=['GET'])
def fetch_notes():
    """
    """
    authorid = request.args.get('authorid', '')
    number = request.args.get('number', 20)
    lastIds = request.args.get('lastIds', "")
    threadid = request.args.get('threadid', '')
    paperid = request.args.get('paperid', '')
    tags = request.args.get('tags', '')
    sort = request.args.get('sort', '')
    direction = request.args.get('direction', '')
    clear = request.args.get('clear', 'false')
    criteria = request.args.get('criteria', '')
    sharedonly = True if request.args.get('sharedonly', 'false')=='true' else False
    #print "clear:", clear

    loadScript = True if lastIds=="" else False

    #print "number:", number, ", lastIds:", lastIds, ", threadid:", threadid, ", paperid:", paperid, ", tags:", tags
    notes = current_app.dbapi.user_timeline(author_id=authorid,
        shared_only=sharedonly, lastIds=lastIds, per_page=number,
        paper_id=paperid, thread_id=threadid, tags=tags,
        sort=sort, direction=direction, criteria=criteria)
    #print 'notes:', notes

    paper = None
    if paperid != '':
        paper = current_app.dbapi.get_papers(paper_id=paperid)[0]


    if len(notes)==0:
        #print "no more!"
        return jsonify(status=False, noMore=True)

    return jsonify(status=True, 
        shared=False if paperid=='' else paper.shared,
        notes=render_template('funnote/itemwidget.html',
            notes = notes,
            loadScript = loadScript,
            shared_view=sharedonly,
            expanded=False
            )
        )
