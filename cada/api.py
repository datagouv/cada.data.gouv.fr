# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify, json, url_for

from cada.models import Advice
from cada.search import search_advices

import requests

api = Blueprint('api', __name__)


@api.route('/')
def doc():
    sample = {
        "advice": Advice.objects.first(),
        "search": sample_search()
    }

    return render_template('api.html', sample=sample)


@api.route('/search')
def search():
    results = search_advices()
    results['advices'] = [_serialize(a) for a in results['advices']]
    return jsonify(results)


@api.route('/<id>/')
def display(id):
    advice = Advice.objects.get_or_404(id=id)
    return jsonify(_serialize(advice))


@api.app_template_filter()
def _serialize(advice):
    return {
        'id': advice.id,
        'administration': advice.administration,
        'type': advice.type,
        'session': advice.session,
        'subject': advice.subject,
        'topics': advice.topics,
        'tags': advice.tags,
        'meanings': advice.meanings,
        'part': advice.part,
        'content': advice.content,
    }


@api.app_template_filter()
def pretty_json(value):
    return json.dumps(obj=value, sort_keys=True, indent=4, separators=(',', ': '))


def init_app(app):
    app.register_blueprint(api, url_prefix='/api')


def sample_search():

    r = requests.get(url_for('api.search', q='Paris', sort='session desc', page_size=3, _external=True))

    return r.json()
