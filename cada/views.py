# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import cStringIO as StringIO
import re

from datetime import datetime

from urlparse import urlsplit, urlunsplit

from flask import abort, render_template, url_for, request, jsonify, Response, flash, redirect
from flask_mail import Attachment
from flask_wtf import Form
from jinja2 import Markup
from werkzeug import url_decode, url_encode
from wtforms import TextField, ValidationError

from cada import app, mail, csv
from cada.models import Advice, PARTS
from cada.search import search_advices, home_data

DEFAULT_PAGE_SIZE = 20

RE_URL = re.compile(r'https?://')


@app.template_global(name='static')
def static_global(filename):
    return url_for('static', filename=filename)


@app.template_global()
@app.template_filter()
def url_rewrite(url=None, **kwargs):
    scheme, netloc, path, query, fragments = urlsplit(url or request.url)
    params = url_decode(query)
    for key, value in kwargs.items():
        params.setlist(key, value if isinstance(value, (list, tuple)) else [value])
    return Markup(urlunsplit((scheme, netloc, path, url_encode(params), fragments)))


@app.template_global()
@app.template_filter()
def url_add(url=None, **kwargs):
    scheme, netloc, path, query, fragments = urlsplit(url or request.url)
    params = url_decode(query)
    for key, value in kwargs.items():
        if not value in params.getlist(key):
            params.add(key, value)
    return Markup(urlunsplit((scheme, netloc, path, url_encode(params), fragments)))


@app.template_global()
@app.template_filter()
def url_del(url=None, *args, **kwargs):
    scheme, netloc, path, query, fragments = urlsplit(url or request.url)
    params = url_decode(query)
    for key in args:
        params.poplist(key)
    for key, value in kwargs.items():
        lst = params.poplist(key)
        if unicode(value) in lst:
            lst.remove(unicode(value))
        params.setlist(key, lst)
    return Markup(urlunsplit((scheme, netloc, path, url_encode(params), fragments)))


@app.template_global()
def in_url(*args, **kwargs):
    scheme, netloc, path, query, fragments = urlsplit(request.url)
    params = url_decode(query)
    return (
        all(arg in params for arg in args)
        and
        all(key in params and params[key] == value for key, value in kwargs.items())
    )


@app.template_global()
@app.template_filter()
def treeize(topics, sep='/'):
    tree = {}
    for topic in topics:
        parts = topic.split(sep)
        if len(parts) == 1:
            tree[topic] = tree.get(topic, [])
        elif len(parts) == 2:
            if not parts[0] in tree:
                tree[parts[0]] = []
            tree[parts[0]].append(parts[1])
    return [(k, v) for k, v in sorted(tree.items())]


@app.template_global()
@app.template_filter()
def treeize_facet(topics, sep='/'):
    tree = {}
    for topic, count, active in topics:
        parts = topic.split(sep)
        if len(parts) == 1:
            tree[topic] = {
                'count': count,
                'active': active,
                'subtopics': tree.get(topic, {}).get('subtopics', [])
            }
        elif len(parts) == 2:
            if not parts[0] in tree:
                tree[parts[0]] = {
                    'count': count,
                    'active': active,
                    'subtopics': []
                }
            tree[parts[0]]['subtopics'].append((parts[1], count, active))
    return [
        (t, tree[t]['count'], tree[t]['active'], tree[t]['subtopics'])
        for t in sorted(tree, key=lambda k: tree[k]['count'])
    ]


@app.template_global()
@app.template_filter()
def part_label(part):
    return PARTS[int(part)]['label']


@app.template_global()
@app.template_filter()
def part_help(part):
    return PARTS[int(part)]['help']


@app.template_global()
def es_date(value):
    return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')


@app.route('/')
def home():
    return render_template('index.html', **home_data())


@app.route('/search')
def search():
    return render_template('search.html', **search_advices())


class AlertAnonForm(Form):
    details = TextField()

    def validate_details(form, field):
        if RE_URL.search(field.data):
            raise ValidationError("Vous ne pouvez pas soumettre d'URL")


@app.route('/<id>/')
def display(id):
    advice = Advice.objects.get_or_404(id=id)
    return render_template('advice.html', advice=advice, form=AlertAnonForm())


@app.route('/<id>/alert', methods=['POST'])
def alert(id):
    advice = Advice.objects.get_or_404(id=id)
    form = AlertAnonForm()
    if form.validate_on_submit():
        csvfile = StringIO.StringIO()
        writer = csv.writer(csvfile)
        writer.writerow(csv.ANON_HEADER)
        writer.writerow(csv.to_anon_row(advice))
        attachment = Attachment(
            'cada-fix-{0}.csv'.format(advice.id),
            'text/csv',
            csvfile.getvalue()
        )
        mail.send_message("Défaut d'anonymisation sur l'avis CADA {0}".format(advice.id),
            recipients=[app.config['ANON_ALERT_MAIL']],
            html=render_template('anon_alert_mail.html', advice=advice, details=form.details.data),
            attachments=[attachment]
        )
        flash(
            "<strong>Merci pour votre contribution!</strong> Nous avons bien pris en compte votre signalement.",
            'success'
        )
        return redirect(url_for('display', id=advice.id))
    else:
        abort(400)


@app.route('/robots.txt')
def robots():
    return Response(render_template('robots.txt'), mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    xml = render_template('sitemap.xml', advices=Advice.objects)
    return Response(xml, mimetype='application/xml')


@app.route('/export')
def export_csv():
    def generate():
        csvfile = StringIO.StringIO()
        writer = csv.writer(csvfile)
        # Generate header
        writer.writerow(csv.HEADER)
        yield csvfile.getvalue()

        for advice in Advice.objects.order_by('id'):
            csvfile = StringIO.StringIO()
            writer = csv.writer(csvfile)
            writer.writerow(csv.to_row(advice))
            yield csvfile.getvalue()

    date = datetime.now().date().isoformat()
    headers = {
        b'Content-Disposition': 'attachment; filename=cada-{0}.csv'.format(date),
        # b'X-Accel-Buffering': 'no',
    }
    response = Response(generate(), mimetype="text/csv", headers=headers)
    return response


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/api/')
def api_doc():
    return render_template('api.html')


@app.route('/api/search')
def api_search():
    results = search_advices()
    results['advices'] = [_serialize(a) for a in results['advices']]
    return jsonify(results)


@app.route('/api/<id>/')
def api_display(id):
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
