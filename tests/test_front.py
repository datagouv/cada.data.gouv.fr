from flask import url_for

from cada import search


def test_render_home_empty(client):
    assert client.get(url_for('site.home')).status_code == 200


def test_render_home_with_content(client, advice_factory):
    for advice in advice_factory.create_batch(3):
        search.index(advice)
    search.es.indices.refresh(index=search.es.index_name)
    assert client.get(url_for('site.home')).status_code == 200


def test_display_advice(client, advice):
    assert client.get(url_for('site.display', id=advice.id)).status_code == 200


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
