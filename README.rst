====
Cada
====

.. image:: https://circleci.com/gh/etalab/cada/tree/master.svg?style=svg
    :target: https://circleci.com/gh/etalab/cada/tree/master
    :alt: Build status

A simplistic interface to search and consult CADA advices.

This is the engine behind http://cada.data.gouv.fr.

Compatibility
=============

CADA has been tested on Python 2.7, MongoDB 2.4+ and ElasticSearch 2.4.

The `ElasticSearch ICU Analysis plugin <https://www.elastic.co/guide/en/elasticsearch/plugins/2.4/analysis-icu.html>`_ is required.

You can install it with:

.. code-block:: console

    bin/plugin install analysis-icu


Installation
============

You can install Cada with pip:

.. code-block:: console

    $ pip install cada


You need to create the cada working directory, designed by ``$HOME`` in this documentation:

.. code-block:: console

    $ mkdir -p $HOME && cd $HOME
    $ vim cada.cfg  # See configuration
    $ wget http://cada.data.gouv.fr/export -O data.csv
    $ cada load data.csv  # Load initial data
    $ cada static  # Optional: collect static assets for proper caching
    $ cada runserver


Configuration
=============
All configuration is done through the ``cada.cfg`` file in ``$HOME``.
It's basically a Python file with constants defined in it:

* ``SERVER_NAME``: the public server name. Mainly used in emails.
* ``SECRET_KEY``: the common crypto hash.Used for session by exemple.
* ``ELASTICSEARCH_URL``: the ElasticSearch server URL in ``host:port`` format. Default to ``localhost:9200`` if not set
* ``MONGODB_SETTINGS``: a dictionary to configure MongoDB. Default to ``{'DB': 'cada'}``. See `the official flask-mongoengine documentation <https://flask-mongoengine.readthedocs.org/en/latest/>`_ for more details.

Mails
-----

Mail server configuration is done through the following variables:

* ``MAIL_SERVER``: SMTP server hostname. Default to ``localhost``.
* ``MAIL_PORT``: SMTP server port. Default to ``25``.
* ``MAIL_USE_TLS``: activate TLS. Default to ``False``.
* ``MAIL_USE_SSL``: activate SSL. Default to ``False``.
* ``MAIL_USERNAME``: optional SMTP server username.
* ``MAIL_PASSWORD``: optional SMTP server password.
* ``MAIL_DEFAULT_SENDER``: Sender email used for mailings. Default to ``cada@localhost``.
* ``ANON_ALERT_MAIL``: destination mail for anonymisation alerts. Default to ``cada.alert@localhost``.

See the `official Flask-Mail documentation <http://pythonhosted.org/flask-mail/#configuring-flask-mail>`_ for more details.

Sentry
------

There is an optional support for Sentry.
You need to install the required dependencies:

.. code-block:: console

    $ pip install raven[flask]
    # Or to install it with cada
    $ pip install cada[sentry]

You need to add your Sentry DSN to the configuration

.. code-block:: python

    SENTRY_DSN = 'https://xxxxx:xxxxxx@sentry.mydomain.com/id'


Piwik
-----

There is an optional Piwik support.
You simply need to add your Piwik server URL and your Piwik project ID to the configuration:

.. code-block:: python

    PIWIK_URL = 'piwik.mydomain.com'
    PIWIK_ID = X
