# -*- coding: utf-8 -*-
from flask_mongoengine import MongoEngine

db = MongoEngine()

PARTS = {
    1: {'label': "Avec audition de l'administration", 'help': "L'administration s'est déplacée à la séance"},
    2: {'label': 'Affaire de principe', 'help': "Etude et avis sur de nouveaux cas"},
    3: {'label': 'Affaire courante', 'help': "Avis sur des cas récurrents"},
    # TODO: ask CADA for proper wording
    4: {'label': 'Délégué', 'help': 'Avis rendu par délégation'},
}


class Advice(db.Document):
    id = db.StringField(primary_key=True)
    administration = db.StringField()
    type = db.StringField()
    session = db.DateTimeField()
    subject = db.StringField()
    topics = db.ListField(db.StringField())
    tags = db.ListField(db.StringField())
    meanings = db.ListField(db.StringField())
    part = db.IntField()
    content = db.StringField()

    def __unicode__(self):
        return self.subject
