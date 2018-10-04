import io

from flask import url_for

from cada import csv


def test_export_csv_empty(client):
    response = client.get(url_for('site.export_csv'))
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert response.is_streamed
    reader = csv.reader(io.BytesIO(response.data))
    assert len([row for row in reader]) == 1


def test_export_csv_with_content(client, advice_factory):
    nb_advices = 3
    advice_factory.create_batch(nb_advices)
    response = client.get(url_for('site.export_csv'))
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert response.is_streamed
    reader = csv.reader(io.BytesIO(response.data))
    assert len([row for row in reader]) == 1 + nb_advices


def test_export_anonymisation_csv(advice):
    row = csv.to_anon_row(advice)
    assert len(row) == 4
    assert row[0] == advice.id
    assert row[1] == url_for('site.display', id=advice.id, _external=True)
