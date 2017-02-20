# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import logging
import shutil

from glob import iglob
from os.path import exists
from sys import exit

from flask_script import Manager, Server, prompt_bool
from webassets.script import CommandLineEnvironment

from cada import create_app, csv
from cada.assets import assets
from cada.models import Advice
from cada.search import es, index

manager = Manager(create_app)

# Turn on debugger by default and reloader
manager.add_command("runserver", Server(
    use_debugger=True,
    use_reloader=True,
    host='0.0.0.0')
)


@manager.option('patterns', nargs='+', help='file patterns to load')
@manager.option('-r', '--reindex', dest="full_reindex", action='store_true',
                help="Trigger a full reindexation")
def load(patterns, full_reindex):
    '''Load a CADA CSV file'''
    for pattern in patterns:
        for filename in iglob(pattern):
            print('Loading', filename)
            with open(filename) as f:
                reader = csv.reader(f)
                # Skip header
                reader.next()
                for idx, row in enumerate(reader, 1):
                    csv.from_row(row)
                    print('.' if idx % 50 else idx, end='')
                print('\nProcessed {0} rows'.format(idx))
    if full_reindex:
        reindex()


@manager.command
def reindex():
    '''Reindex all advices'''
    print('Deleting index {0}'.format(es.index_name))
    if es.indices.exists(es.index_name):
        es.indices.delete(index=es.index_name)
    es.initialize()

    idx = 0
    for idx, advice in enumerate(Advice.objects, 1):
        index(advice)
        print('.' if idx % 50 else idx, end='')

    es.indices.refresh(index=es.index_name)
    print('\nIndexed {0} advices'.format(idx))


@manager.option('path', nargs='?', default='static', help='target path')
@manager.option('-ni', '--no-input', dest="input",
                action='store_false', help="Disable input prompts")
def static(path, input):
    '''Compile and collect static files'''
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)

    cmdenv = CommandLineEnvironment(assets, log)
    cmdenv.build()

    if exists(path):
        print('"{0}" directory already exists and will be erased'.format(path))
        if input and not prompt_bool('Are you sure'):
            exit(-1)
        shutil.rmtree(path)

    print('Copying assets into "{0}"'.format(path))
    shutil.copytree(assets.directory, path)

    print('Done')


@manager.command
def anon():
    '''Check for candidates to anonymization'''
    filename = 'urls_to_check.csv'

    candidates = Advice.objects(__raw__={
        '$or': [
            {'subject': {
                '$regex': '(Monsieur|Madame|Docteur|Mademoiselle)\s+[^X\s\.]{3}',
                '$options': 'imx',
            }},
            {'content': {
                '$regex': '(Monsieur|Madame|Docteur|Mademoiselle)\s+[^X\s\.]{3}',
                '$options': 'imx',
            }}
        ]
    })

    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        # Generate header
        writer.writerow(csv.ANON_HEADER)

        for idx, advice in enumerate(candidates):
            writer.writerow(csv.to_anon_row(advice))
            print('.' if idx % 50 else idx, end='')
        print('')

    print('Total: {0} candidates'.format(len(candidates)))


@manager.command
@manager.option('filename', nargs='?', default='fix.csv')
def fix(filename):
    bads = []
    with open(filename) as csvfile:
        reader = csv.reader(csvfile)
        reader.next()  # Skip header
        for id, _, sources, dests in reader:
            advice = Advice.objects.get(id=id)
            sources = [s.strip() for s in sources.split(',') if s.strip()]
            dests = [d.strip() for d in dests.split(',') if d.strip()]
            if not len(sources) == len(dests):
                bads.append(id)
                continue
            for source, dest in zip(sources, dests):
                print('{0}: Replace {1} with {2}'.format(id, source, dest))
                advice.subject = advice.subject.replace(source, dest)
                advice.content = advice.content.replace(source, dest)
            advice.save()
            index(advice)
        print('')
    for id in bads:
        print('{0}: Replacements length not matching'.format(id))
    print('\nDone')


def main():
    manager.run()
