import pytest

from flask import url_for

from cada import search
from cada.models import PARTS
from cada.views import mail


def test_render_home_empty(client):
    assert client.get(url_for('site.home')).status_code == 200


def test_render_home_with_content(client, advice_factory):
    for advice in advice_factory.create_batch(3):
        search.index(advice)
    search.es.indices.refresh(index=search.es.index_name)
    assert client.get(url_for('site.home')).status_code == 200


@pytest.mark.parametrize('advice__part', PARTS.keys())
def test_display_advice(client, advice):
    assert client.get(url_for('site.display', id=advice.id)).status_code == 200


def test_alert_advice(app, client, advice):
    with mail.record_messages() as mails:
        response = client.post(url_for('site.alert', id=advice.id), data={
            'details': 'somedetails'
        })
    assert response.status_code == 302
    assert response.location == url_for('site.display', id=advice.id, _external=True)
    assert len(mails) == 1
    sent_mail = mails[0]
    assert sent_mail.recipients == [app.config['ANON_ALERT_MAIL']]
    assert len(sent_mail.attachments) == 1
    attachment = sent_mail.attachments[0]
    assert attachment.filename == 'cada-fix-{}.csv'.format(advice.id)
    assert attachment.content_type == 'text/csv'


def test_alert_advice_requires_details(client, advice):
    response = client.post(url_for('site.alert', id=advice.id), data={})
    assert response.status_code == 400


def test_alert_advice_prevent_spam_urls(client, advice):
    response = client.post(url_for('site.alert', id=advice.id), data={
        'details': 'Details is not allowed to have an url https://company.com/spam'
    })
    assert response.status_code == 400


def test_search_empty(client):
    assert client.get(url_for('site.search')).status_code == 200


def test_search_with_content(client, advice_factory):
    for advice in advice_factory.create_batch(3):
        search.index(advice)
    search.es.indices.refresh(index=search.es.index_name)
    assert client.get(url_for('site.search')).status_code == 200


def test_sitemap(client, advice_factory):
    advice_factory.create_batch(3)
    assert client.get(url_for('site.sitemap')).status_code == 200


def test_robots_txt(client):
    assert client.get(url_for('site.robots')).status_code == 200
