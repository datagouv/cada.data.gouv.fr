#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from os.path import exists, join


class DefaultConfig(object):
    MONGODB_HOST = 'localhost'
    MONGODB_DB = 'cada'
    SECRET_KEY = 'no-secret-this-is-open'
    MAIL_DEFAULT_SENDER = 'cada@locahost'
    ANON_ALERT_MAIL = 'cada.alert@locahost'


def create_app(config=None):
    from flask import Flask

    from cada import views, api
    from cada.assets import assets
    from cada.models import db
    from cada.search import es

    app = Flask('cada')

    app.config.from_object(DefaultConfig)
    app.config.from_envvar('CADA_CONFIG', silent=True)

    custom_settings = join(os.getcwd(), 'cada.cfg')
    if exists(custom_settings):
        app.config.from_pyfile(custom_settings)

    if config:
        app.config.from_object(config)

    # Optionnal Sentry support
    if 'SENTRY_DSN' in app.config:
        from raven.contrib.flask import Sentry
        Sentry(app)

    db.init_app(app)
    es.init_app(app)
    assets.init_app(app)
    views.init_app(app)
    api.init_app(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
