# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, jsonify

from cada.models import Advice
from cada.search import search_advices


api = Blueprint('api', __name__)


@api.route('/')
def doc():
    sample = Advice.objects.first()
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


def init_app(app):
    app.register_blueprint(api, url_prefix='/api')
