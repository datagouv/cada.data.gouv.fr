# -*- coding: utf-8 -*-
import logging

from datetime import datetime

from elasticsearch import Elasticsearch
from flask import current_app, request

from cada.models import Advice

log = logging.getLogger(__name__)

MAPPING = {
    "properties": {
        "id": {"type": "text", "index": "true"},
        "administration": {
            "type": "text",
            "analyzer": "fr_analyzer",
            "fields": {
                "raw": {"type": "text", "index": "false"},
                "keyword": {"type": "keyword"},
            },
        },
        "type": {"type": "text", "index": "false"},
        "session": {
            "type": "date",
            "format": "yyyy-MM-dd",
            "store": "true",
            "fields": {
                "raw": {"type": "text", "index": "false"},
                "keyword": {"type": "keyword"},
            },
        },
        "subject": {
            "type": "text",
            "analyzer": "fr_analyzer",
            "fields": {
                "raw": {"type": "text", "index": "false"},
                "keyword": {"type": "keyword"},
            },
        },
        "topics": {
            "type": "text",
            "analyzer": "fr_analyzer",
            "fields": {
                "raw": {"type": "text", "index": "false"},
                "keyword": {"type": "keyword"},
            },
        },
        "tags": {
            "type": "text",
            "index": "false",
            "fields": {
                "raw": {"type": "text", "index": "false"},
                "keyword": {"type": "keyword"},
            },
        },
        "meanings": {
            "type": "text",
            "index": "false",
            "fields": {
                "raw": {"type": "text", "index": "false"},
                "keyword": {"type": "keyword"},
            },
        },
        "part": {"type": "short"},
        "content": {
            "type": "text",
            "analyzer": "fr_analyzer",
            "fields": {"raw": {"type": "text", "index": "false"}},
        },
    }
}

FIELDS = (
    "id^5",
    "subject^4",
    "content^3",
    "administration",
    "topics",
    "tags.keyword",
)

SORTS = {
    "topic": "topics.raw",
    "administration": "administration.raw",
    "session": "session",
}

FACETS = {
    "administration": "administration.keyword",
    "tag": "tags.keyword",
    "topic": "topics.keyword",
    "session": "session.keyword",
    "part": "part",
    "meaning": "meanings.keyword",
}

ANALYSIS = {
    "filter": {
        "fr_stop_filter": {"type": "stop", "stopwords": ["_french_"]},
        "fr_stem_filter": {"type": "stemmer", "name": "minimal_french"},
    },
    "analyzer": {
        "fr_analyzer": {
            "type": "custom",
            "tokenizer": "icu_tokenizer",
            "filter": [
                "icu_folding",
                "icu_normalizer",
                "fr_stop_filter",
                "fr_stem_filter",
            ],
            "char_filter": ["html_strip"],
        }
    },
}


DOCTYPE = "advice"
DEFAULT_PAGE_SIZE = 20


class ElasticSearch(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault("ELASTICSEARCH_URL", "localhost:9200")
        app.extensions["elasticsearch"] = Elasticsearch(
            [app.config["ELASTICSEARCH_URL"]]
        )

    def __getattr__(self, item):
        if "elasticsearch" not in current_app.extensions.keys():
            raise Exception("not initialised, did you forget to call init_app?")
        return getattr(current_app.extensions["elasticsearch"], item)

    @property
    def index_name(self):
        if current_app.config.get("TESTING"):
            return "{0}-test".format(current_app.name)
        return current_app.name

    def initialize(self):
        """Create or update indices and mappings"""
        if es.indices.exists(self.index_name):
            es.indices.put_mapping(
                index=self.index_name, doc_type=DOCTYPE, body=MAPPING
            )
        else:
            es.indices.create(
                index=self.index_name,
                body={
                    "mappings": MAPPING,
                    "settings": {"analysis": ANALYSIS},
                },
            )


es = ElasticSearch()


def build_text_queries():
    if not request.args.get("q"):
        return ""
    query_string = request.args.get("q")
    if isinstance(query_string, (list, tuple)):
        query_string = " ".join(query_string)

    print(query_string)
    return [
        {
            "query_string": {
                "query": query_string,
                "default_operator": "AND",
                "fields": FIELDS,
            }
        }
    ]


def build_facet_queries():
    queries = []
    for name, field in FACETS.items():
        if name in request.args:
            for term in request.args.getlist(name):
                queries.append({"term": {field: term}})
    return queries


def build_query():
    must = []
    must.extend(build_text_queries())
    must.extend(build_facet_queries())
    return {"bool": {"must": must}} if must else {"match_all": {}}


def build_aggs():
    return dict(
        [
            (name, {"terms": {"field": field, "size": 10}})
            for name, field in FACETS.items()
        ]
    )


def build_sort():
    """Build sort query paramter from kwargs"""
    sorts = request.args.getlist("sort")
    sorts = [sorts] if isinstance(sorts, str) else sorts
    sorts = [s.split(" ") for s in sorts]
    return [{SORTS[s]: d} for s, d in sorts if s in SORTS]


def search_advices():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = int(request.args.get("page_size", DEFAULT_PAGE_SIZE))
    start = (page - 1) * page_size

    result = es.search(
        index=es.index_name,
        body={
            "track_total_hits": True,
            "query": build_query(),
            "aggs": build_aggs(),
            "from": start,
            "size": page_size,
            "sort": build_sort(),
        },
    )

    ids = [hit["_id"] for hit in result.get("hits", {}).get("hits", [])]
    advices = Advice.objects.in_bulk(ids)
    advices = [advices[id] for id in ids]

    facets = {}
    for name, content in result.get("aggregations", {}).items():
        actives = request.args.get(name)
        actives = [actives] if isinstance(actives, str) else actives or []
        facets[name] = [
            (term["key"], term["doc_count"], term["key"] in actives)
            for term in content.get("buckets", [])
        ]

    return {
        "advices": advices,
        "facets": facets,
        "page": page,
        "page_size": page_size,
        "total": result["hits"]["total"]["value"],
    }


def agg_to_list(result, facet):
    return [
        (t["key"], t["doc_count"])
        for t in result.get("aggregations", {}).get(facet, {}).get("buckets", [])
    ]


def ts_to_dt(value):
    """Convert an elasticsearch timestamp into a Python datetime"""
    if not value:
        return
    return datetime.utcfromtimestamp(value * 1e-3)


def home_data():
    result = es.search(
        es.index_name,
        body={
            "query": {"match_all": {}},
            "size": 0,
            "track_total_hits": True,
            "aggs": {
                "tags": {"terms": {"field": "tags.keyword", "size": 20}},
                "topics": {
                    "terms": {
                        "field": "topics.keyword",
                        "exclude": "/*",  # Exclude subtopics
                        "size": 20,
                    }
                },
                "sessions": {"stats": {"field": "session"}},
            },
        },
    )

    sessions = result.get("aggregations", {}).get("sessions", {})

    return {
        "topics": agg_to_list(result, "topics"),
        "tag_cloud": agg_to_list(result, "tags"),
        "total": result["hits"]["total"]["value"],
        "sessions": {
            "from": ts_to_dt(sessions.get("min")),
            "to": ts_to_dt(sessions.get("max")),
        },
    }


def index(advice):
    """Index/Reindex a CADA advice"""
    topics = []
    for topic in advice.topics:
        topics.append(topic)
        parts = topic.split("/")
        if len(parts) > 1:
            topics.append(parts[0])

    try:
        es.index(
            index=es.index_name,
            id=advice.id,
            body={
                "id": advice.id,
                "administration": advice.administration,
                "type": advice.type,
                "session": advice.session.strftime("%Y-%m-%d"),
                "subject": advice.subject,
                "topics": topics,
                "tags": advice.tags,
                "meanings": advice.meanings,
                "part": advice.part,
                "content": advice.content,
            },
        )
    except Exception:
        log.exception("Unable to index advice %s", advice.id)
