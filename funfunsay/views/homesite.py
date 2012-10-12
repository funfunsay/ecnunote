# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime
import time
import random

from flask import (Blueprint, render_template, current_app, request,
                   flash, url_for, redirect, session, g, abort, make_response,
                   send_file, jsonify)
from jinja2 import TemplateNotFound
from werkzeug import check_password_hash, generate_password_hash
from funfunsay.forms import (SignupForm, LoginForm, RecoverPasswordForm,
                         ChangePasswordForm, ReauthForm, UProfileForm)
from flask.ext.babel import gettext as _
from flask.ext.login import (login_required, login_user, current_user,
                            logout_user, confirm_login, fresh_login_required,
                            login_fresh)

from funfunsay.models import User
from funfunsay.extensions import cache
from funfunsay.config import DefaultConfig, APP_NAME
from funfunsay.extensions import mongo


homesite = Blueprint('homesite', __name__
                       #, url_prefix='/pl'
                       #,static_folder='/static'
                       )

@homesite.route('/')
def home():
    if request.url.find('ECNU')!=-1 and request.url.find('www.ECNU')==-1:
        #print "redirect ECNU to www.ECNU."
        url = request.url.replace('ECNU', 'www.ECNU')
        return redirect(url)

    login_form = signup_form = None
    if not current_user.is_authenticated():
        login_form= LoginForm(next=request.args.get('next'))
        signup_form = SignupForm(nex=request.args.get('next'))

    return render_template('index.html', 
        login_form=login_form,signup_form=signup_form)

@homesite.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(login=request.args.get('login', None),
                     next=request.args.get('next', None))

    if form.validate_on_submit():
        user, authenticated, error = User.authenticate(
            form.login.data,form.password.data)

        if user and authenticated:
            remember = request.form.get('remember') == 'y'
            if login_user(user, remember=remember):
                flash(_("Logged in!"), 'success')
                
            return redirect(form.next.data or url_for('homesite.home'))
        else:
            flash(_('Sorry, invalid login'), 'error')

    return render_template('login.html', form=form)

default_note_source = u"""
欢迎使用可聚合分享的云笔记本
====

　　可聚合分享的云笔记本系统采用Markdown作为文本编辑和保存的格式。让您更容易的整理自己的文字，通过细粒度的笔记条目组成完整的文章。基本的功能包括：

  - **创建笔记**。
  - **通过脉络（Threads）组织**。将笔记归入不同的脉络，例如*生活*、*工作*、*学习*以及*旅游*等。
  - **创建文章（Paper）**。创建文章并且从已有笔记中选择纳入相关的笔记。
  - **文章编排**。系统支持对文章中的笔记进行拖动排序。
  - **笔记共享**。笔记通过文章的形式共享（文章可以共享，同时文章中的笔记需单独设置共享后才能随着文章一起共享）。
  - **笔记收纳（Take in）功能**。用户还可以收纳（Take in）其他用户共享的文章中的笔记，作为自己的一条笔记。
"""
@homesite.route('/register', methods=['GET', 'POST'])
def register():
    login_form= LoginForm(next=request.args.get('next'))
    form = SignupForm(next=request.args.get('next'))

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)

        userDoc = current_app.dbapi.update_user_profile(user_id=form.name.data,
            name=form.name.data, email=form.email.data, 
            new_pw_hash=generate_password_hash(form.password.data),
            invitation_code=form.invitation_code.data,
            upsert=True,
            )
        #print userDoc
        #todo: check fail
        flash(_('You were successfully registered and can login now'))
        user, authenticated, error = User.authenticate(
            form.name.data, form.password.data)

        #print "You were successfully registered and can login now"

        if login_user(user):
           current_app.dbapi.add_note(author_id=current_user.id, source=default_note_source)
           return redirect(form.next.data or url_for('funnote.fastnote'))
            #return redirect( url_for('funnote.index') )
    else:
        pass
        #print "validate failed."

    return render_template('register.html', form=form, login_form=login_form)

@homesite.route('/logout')
def logout(): 
    """Logs the user out."""
    logout_user()
    flash(_('You were logged out'))
    session.pop('user_id', None)
    return redirect(url_for('homesite.home'))

@homesite.route('/search')
def search():
    return render_template('search.html')

@homesite.route('/user_profile')
@login_required
def user_profile():
    invitation_code = request.args.get('invitation_code', '')
    #print invitation_code
    invitates = mongo.db.invitates.find({"author_id":current_user.id})
    return render_template('uprofile.html', 
        user = current_app.dbapi.get_user_profile(id=current_user.id),
        invitation_code=invitation_code, invitates=invitates)


@homesite.route('/_unlink_provider')
@login_required
def unlink_provider():
    invitation_code = request.args.get('invitation_code', '')
    #print invitation_code
    invitates = mongo.db.invitates.find({"author_id":current_user.id})
    user_id_provider = request.args.get('user_id_provider')
    user_id = current_user.id
    provider = request.args.get('provider')

    user = current_app.dbapi.remove_provider(user_id=user_id, 
        user_id_provider=user_id_provider, 
        provider=provider)

    print user.providers

    return render_template('uprofile.html', 
        user = user,
        invitation_code=invitation_code, invitates=invitates)


@homesite.route('/generate_invitation_code')
@login_required
def generate_invitation_code():
    cur_time = int(time.time())
    # Add a random number to avoid different user generate code simultaneously
    # though it is almost impossible
    code = hex(int(str(cur_time)[::-1]) + random.randint(1, 100))[2:10]
    #print code
    code_doc = User.new_invitation_code_document(current_user.id, code)
    mongo.db.invitates.insert(code_doc)

    return redirect(url_for('homesite.user_profile', invitation_code=code))


