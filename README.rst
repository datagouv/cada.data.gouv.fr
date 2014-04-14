====
Cada
====

.. image:: https://pypip.in/version/cada/badge.png
    :target: https://pypi.python.org/pypi/cada/
    :alt: Latest Version
.. image:: https://pypip.in/download/cada/badge.png
    :target: https://pypi.python.org/pypi/cada/
    :alt: Downloads

A simplistic interface to search and consult CADA advices.

This is the engine behing http://cada.data.gouv.fr.

Compatibility
=============

CADA has been tested on Python 2.7, MongoDB 2.4+ and ElasticSearch 1.1.

The `ElasticSearch ICU Analysis plugin <http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/analysis-icu-plugin.html>`_ is required.

You can install it with:

.. code-block:: console

    bin/plugin -install elasticsearch/elasticsearch-analysis-icu/2.1.0


Installation
============

You can install Cada with pip:

.. code-block:: console

    $ pip install cada

or with easy_install:

.. code-block:: console

    $ easy_install cada


You need to create the cada working directory, designed by ``$HOME`` in this documentation:

.. code-block:: console

    $ mkdir -p $HOME && cd $HOME
    $ vim cada.cfg  # See configuration
    $ wget http://cada.data.gouv.fr/export -O data.csv
    $ cada load data.csv  # Load initial data
    $ cada static  # Optionnal: collect static assets for proper caching
    $ cada runserver


Configuration
=============
All configuration is done trhough the ``cada.cfg`` file in ``$HOME``.
It's basically a Python file with constants defined in it:

* ``SERVER_NAME``: the public server name. Mainly used in emails.
* ``SECRET_KEY``: the common crypto hash.Used for session by exemple.
* ``ELASTICSEARCH_URL``: the ElasticSearch server URL in ``host:port`` format. Default to ``localhost:9200`` if not set
* ``MONGODB_SETTINGS``: a dictionnary to configure MongoDB. Default to ``{'DB': 'cada'}``. See `the official flask-mongoengine documentation <https://flask-mongoengine.readthedocs.org/en/latest/>`_ for more details.

Mails
-----

Mail server configuration is done through the following variables:

* ``MAIL_SERVER``: SMTP server hostname. Default to ``localhost``.
* ``MAIL_PORT``: SMTP server port. Default to ``25``.
* ``MAIL_USE_TLS``: activate TLS. Default to ``False``.
* ``MAIL_USE_SSL``: activate SSL. Default to ``False``.
* ``MAIL_USERNAME``: optionnal SMTP server username.
* ``MAIL_PASSWORD``: optionnal SMTP server password.
* ``MAIL_DEFAULT_SENDER``: Sender email used for mailings. Default to ``cada@localhost``.
* ``ANON_ALERT_MAIL``: destination mail for anonimysation alerts. Default to ``cada.alert@localhost``.

See the `official Flask-Mail documentation <http://pythonhosted.org/flask-mail/#configuring-flask-mail>`_ for more details.

Sentry
------

There is an optionnal support for Sentry.
You need to install the required dependencies:

.. code-block:: console

    $ pip install raven[flask]
    # Or, to install it with cada
    $ pip install cada[sentry]

You need to add your Sentry DSN to the configuration

.. code-block:: python

    SENTRY_DSN = 'https://xxxxx:xxxxxx@sentry.mydomain.com/id'


Piwik
-----

There is an optionnal Piwik support.
You simply need to add your Piwik server URL and your Piwik project ID to the configuration:

.. code-block:: python

    PIWIK_URL = 'piwik.mydomain.com'
    PIWIK_ID = X

