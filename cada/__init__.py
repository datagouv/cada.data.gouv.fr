#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from os.path import exists, join

from flask import Flask
from flask_mongoengine import MongoEngine
from flask_assets import Environment, Bundle
from flask_mail import Mail


class DefaultConfig(object):
    MONGODB_SETTINGS = {'DB': 'cada'}
    SECRET_KEY = 'no-secret-this-is-open'
    MAIL_DEFAULT_SENDER = 'cada@locahost'
    ANON_ALERT_MAIL = 'cada.alert@locahost'


app = Flask(__name__)

app.config.from_object(DefaultConfig)
app.config.from_envvar('CADA_CONFIG', silent=True)

custom_settings = join(os.getcwd(), 'cada.cfg')
if exists(custom_settings):
    app.config.from_pyfile(custom_settings)

db = MongoEngine(app)
assets = Environment(app)
mail = Mail(app)

js_bundle = Bundle('js/jquery.js', 'js/bootstrap.js', 'js/placeholders.jquery.js', 'js/cada.js',
    filters='rjsmin', output='js/cada.min.js')

api_js_bundle = Bundle('js/api.js',
    filters='rjsmin', output='js/api.min.js')

css_bundle = Bundle('css/bootstrap.flatly.css', 'css/cada.css',
    filters='cssmin', output='css/cada.min.css')

assets.register('js', js_bundle)
assets.register('js-api', api_js_bundle)
assets.register('css', css_bundle)

# Optionnal Sentry support
if 'SENTRY_DSN' in app.config:
    from raven.contrib.flask import Sentry
    sentry = Sentry(app)

from cada import models, search, views


if __name__ == '__main__':
    app.run()
