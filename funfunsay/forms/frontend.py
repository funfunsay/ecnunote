# -*- coding: utf-8 -*-

from flask.ext.wtf import (Form, HiddenField, BooleanField, TextField,
                          PasswordField, SubmitField, TextField, TextAreaField,
                          ValidationError, required, equal_to, email,
                          length)
from flask import (Flask, g)
import time
from flask.ext.babel import gettext, lazy_gettext as _

from funfunsay.models import User

PASSLEN_MIN = 1
PASSLEN_MAX = 16

class LoginForm(Form):
    next = HiddenField()
    remember = BooleanField(_('Remember me'))
    login = TextField(_('Username or email address'), [required()])
    password = PasswordField(_('Password'), [required(), length(min=PASSLEN_MIN, max=PASSLEN_MAX)])
    submit = SubmitField(_('Login'))


class SignupForm(Form):
    next = HiddenField()
    name = TextField(_('Username'), [required()])
    password = PasswordField(_('Password'), [required(), length(min=PASSLEN_MIN, max=PASSLEN_MAX)])
    password_again = PasswordField(_('Password again'), [required(), length(min=PASSLEN_MIN, max=PASSLEN_MAX), equal_to('password')])
    email = TextField(_('Email address'), [required(), email(message=_('A valid email address is required'))])
    invitation_code = TextField(_('Invitation Code'), [required(message=_('Please fill in the invitation code!'))])
    submit = SubmitField(_('Signup'))

    def validate_name(self, field):
        if g.db.users.find_one({"_id":field.data}) is not None:
            raise ValidationError, _('This username is taken')

    def validate_email(self, field):
        if g.db.users.find_one({"email":field.data}) is not None:
            raise ValidationError, _('This email is taken')

    def validate_invitation_code(self, field):
        if g.db.invitates.find_one({"code":field.data, "used":'False'}) is None:
            raise ValidationError, _('Invalid code')


class RecoverPasswordForm(Form):
    email = TextField(_('Your email'), validators=[
                      email(message=_('A valid email address is required'))])
    submit = SubmitField(_('Send instructions'))


class ChangePasswordForm(Form):
    activation_key = HiddenField()
    password = PasswordField('Password', validators=[
                             required(message=_('Password is required'))])
    password_again = PasswordField(_('Password again'), validators=[
                                   equal_to('password', message=\
                                            _("Passwords don't match"))])
    submit = SubmitField(_('Save'))


class ReauthForm(Form):
    next = HiddenField()
    password = PasswordField(_('Password'), [required(), length(min=PASSLEN_MIN, max=PASSLEN_MAX)])
    submit = SubmitField(_('Reauthenticate'))


class TwitterbookForm(Form):
    next = HiddenField()
    title = TextField(_('Title of your new twitterbook'), [required()])
    description = TextField(_('Description of your new twitterbook'), [required()])
    submit = SubmitField(_('Create'))
    

class UProfileForm(Form):
    name = TextField(_('Username'), [required()])
    password = PasswordField(_('Password'), [required(), length(min=PASSLEN_MIN, max=PASSLEN_MAX)])
    password_again = PasswordField(_('Password again'), [required(), length(min=PASSLEN_MIN, max=PASSLEN_MAX), equal_to('password')])
    email = TextField(_('Email address'), [required(), email(message=_('A valid email address is required'))])
    submit = SubmitField(_('Commit'))

    def validate_email(self, field):
        if g.db.users.find_one({"email":field.data}) is not None:
            raise ValidationError, _('This email is taken')

