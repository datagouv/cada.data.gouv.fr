import pytest

from flask import url_for

from cada import search
from cada.models import PARTS


def test_api_doc_empty(client):
    assert client.get(url_for('api.doc')).status_code == 200


def test_api_doc_wih_advices(client, advice_factory):
    advice_factory.create_batch(3)
    assert client.get(url_for('api.doc')).status_code == 200


def test_search_empty(client):
    assert client.get(url_for('api.search')).status_code == 200


def test_search_with_content(client, advice_factory):
    for advice in advice_factory.create_batch(3):
        search.index(advice)
    search.es.indices.refresh(index=search.es.index_name)
    response = client.get(url_for('api.search'))
    assert response.status_code == 200
    assert len(response.json['advices']) == 3


@pytest.mark.parametrize('advice__part', PARTS.keys())
def test_display_advice(client, advice):
    response = client.get(url_for('api.display', id=advice.id))
    assert response.status_code == 200
    assert response.json['id'] == advice.id
    assert response.json['subject'] == advice.subject
