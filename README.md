# CADA

[![Build status][circleci-badge]][circleci-url]
[![Join the chat at https://gitter.im/etalab/cada][gitter-badge]][gitter-url]


A simplistic interface to search and consult CADA advices.

This is the engine behind https://cada.data.gouv.fr.

## Compatibility

CADA has been tested on Python 3.7, MongoDB 4.1 and ElasticSearch 7.2.

The [ElasticSearch ICU Analysis plugin](https://www.elastic.co/guide/en/elasticsearch/plugins/2.4/analysis-icu.html) is required.

You can install it with:

```console
elasticsearch-plugin install analysis-icu
```

## Installation

You can install Cada with pip:

```bash
$ pip install cada
```

You need to create the cada working directory, denoted by ``$HOME`` in this documentation:

```bash
$ mkdir -p $HOME && cd $HOME
$ vim cada.cfg  # See configuration
$ wget https://cada.data.gouv.fr/export -O data.csv
$ cada load data.csv  # Load initial data
$ cada static  # Optional: collect static assets for proper caching
$ cada runserver
```

### local development environment

Please make sure you are in a clean [virtualenv](https://virtualenv.pypa.io/en/stable/).

```bash
$ git clone https://github.com/etalab/cada
$ cd cada
$ docker-compose up -d
$ pip install -e .
$ wget https://cada.data.gouv.fr/export -O data.csv
$ cada load data.csv
$ cada reindex
$ cada runserver
```


## Configuration
All configuration is done through the ``cada.cfg`` file in ``$HOME``.
It's basically a Python file with constants defined in it:

* ``SERVER_NAME``: the public server name. Mainly used in emails.
* ``SECRET_KEY``: the common crypto hash. e.g. sessions. `openssl rand -hex 24` should be a good start.
* ``ELASTICSEARCH_URL``: the ElasticSearch server URL in ``host:port`` format. Default to ``localhost:9200`` if not set
* ``MONGODB_SETTINGS``: a dictionary to configure MongoDB. Default to ``{'DB': 'cada'}``. See [the official flask-mongoengine documentation](https://flask-mongoengine.readthedocs.org/en/latest/) for more details.

### Mails

Mail server configuration is done through the following variables:

* ``MAIL_SERVER``: SMTP server hostname. Default to ``localhost``.
* ``MAIL_PORT``: SMTP server port. Default to ``25``.
* ``MAIL_USE_TLS``: activate TLS. Default to ``False``.
* ``MAIL_USE_SSL``: activate SSL. Default to ``False``.
* ``MAIL_USERNAME``: optional SMTP server username.
* ``MAIL_PASSWORD``: optional SMTP server password.
* ``MAIL_DEFAULT_SENDER``: Sender email used for mailings. Default to ``cada@localhost``.
* ``ANON_ALERT_MAIL``: destination mail for anonymisation alerts. Default to ``cada.alert@localhost``.

See the [official Flask-Mail documentation](http://pythonhosted.org/flask-mail/#configuring-flask-mail) for more details.

### Sentry

There is an optional support for Sentry.
You need to install the required dependencies:

```bash
$ pip install raven[flask]
# Or to install it with cada
$ pip install cada[sentry]
```

You need to add your Sentry DSN to the configuration

```python
SENTRY_DSN = 'https://xxxxx:xxxxxx@sentry.mydomain.com/id'
```


### Piwik

There is an optional Piwik support.
You simply need to add your Piwik server URL and your Piwik project ID to the configuration:

```python
PIWIK_URL = 'piwik.mydomain.com'
PIWIK_ID = X
```

[circleci-url]: https://circleci.com/gh/etalab/cada
[circleci-badge]: https://circleci.com/gh/etalab/cada.svg?style=shield
[gitter-badge]: https://badges.gitter.im/Join%20Chat.svg
[gitter-url]: https://gitter.im/etalab/cada
