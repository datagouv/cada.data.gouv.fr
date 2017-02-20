#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask_assets import Environment, Bundle

assets = Environment()

js_bundle = Bundle('js/jquery.js', 'js/bootstrap.js', 'js/placeholders.jquery.js', 'js/cada.js',
                   filters='rjsmin', output='js/cada.min.js')

api_js_bundle = Bundle('js/api.js',
                       filters='rjsmin', output='js/api.min.js')

css_bundle = Bundle('css/bootstrap.flatly.css', 'css/cada.css',
                    filters='cssmin', output='css/cada.min.css')

assets.register('js', js_bundle)
assets.register('js-api', api_js_bundle)
assets.register('css', css_bundle)
