import io
import pytest

from flask import url_for

from cada import csv
from cada.models import PARTS


def test_export_csv_empty(client):
    response = client.get(url_for('site.export_csv'))
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert response.is_streamed
    reader = csv.reader(io.StringIO(response.data.decode('utf8')))
    assert len([row for row in reader]) == 1


@pytest.mark.parametrize('advice__part', PARTS.keys())
def test_export_csv_with_content(client, advice, advice_factory):
    nb_advices = 3
    total_advices = nb_advices + 1  # One is already created to test all parts
    advice_factory.create_batch(nb_advices)
    response = client.get(url_for('site.export_csv'))
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert response.is_streamed
    reader = csv.reader(io.StringIO(response.data.decode('utf8')))
    assert len([row for row in reader]) == 1 + total_advices  # Include headers


@pytest.mark.parametrize('advice__part', PARTS.keys())
def test_export_anonymisation_csv(advice):
    row = csv.to_anon_row(advice)
    assert len(row) == 4
    assert row[0] == advice.id
    assert row[1] == url_for('site.display', id=advice.id, _external=True)
