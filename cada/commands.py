# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import click
import logging
import pkg_resources
import shutil
import sys

from glob import iglob
from os.path import exists

from webassets.script import CommandLineEnvironment
from flask.cli import FlaskGroup, shell_command, run_command, routes_command

from cada import create_app, csv
from cada.assets import assets
from cada.models import Advice
from cada.search import es, index

log = logging.getLogger(__name__)

OK = '✔'.encode('utf8')
KO = '✘'.encode('utf8')
INFO = '➢'.encode('utf8')
WARNING = '⚠'.encode('utf8')
HEADER = '✯'.encode('utf8')

NO_CAST = (int, float, bool)

CONTEXT_SETTINGS = {
    'auto_envvar_prefix': 'cada',
    'help_option_names': ['-?', '-h', '--help'],
}

click.disable_unicode_literals_warning = True


def safe_unicode(string):
    '''Safely transform any object into utf8 encoded bytes'''
    if not isinstance(string, basestring):
        string = unicode(string)
    if isinstance(string, unicode):
        string = string.encode('utf8')
    return string


def color(name, **kwargs):
    return lambda t: click.style(safe_unicode(t), fg=name, **kwargs).decode('utf8')


green = color('green', bold=True)
yellow = color('yellow', bold=True)
red = color('red', bold=True)
cyan = color('cyan', bold=True)
magenta = color('magenta', bold=True)
white = color('white', bold=True)


def echo(msg, *args, **kwargs):
    '''Wraps click.echo, handles formatting and check encoding'''
    file = kwargs.pop('file', None)
    nl = kwargs.pop('nl', True)
    err = kwargs.pop('err', False)
    color = kwargs.pop('color', None)
    msg = safe_unicode(msg.format(*args, **kwargs))
    click.echo(msg, file=file, nl=nl, err=err, color=color)


def header(msg, *args, **kwargs):
    '''Display an header'''
    msg = ' '.join((yellow(HEADER), white(msg), yellow(HEADER)))
    echo(msg, *args, **kwargs)


def success(msg, *args, **kwargs):
    '''Display a success message'''
    echo('{0} {1}'.format(green(OK), white(msg)), *args, **kwargs)


def warning(msg, *args, **kwargs):
    '''Display a warning message'''
    msg = '{0} {1}'.format(yellow(WARNING), msg)
    echo(msg, *args, **kwargs)


def error(msg, details=None, *args, **kwargs):
    '''Display an error message with optionnal details'''
    msg = '{0} {1}'.format(red(KO), white(msg))
    if details:
        msg = '\n'.join((msg, safe_unicode(details)))
    echo(format_multiline(msg), *args, **kwargs)


def exit_with_error(msg='Aborted', details=None, code=-1, *args, **kwargs):
    '''Exit with error'''
    error(msg, details=details, *args, **kwargs)
    sys.exit(code)


def format_multiline(string):
    string = string.replace('\n', '\n│ ')
    return replace_last(string, '│', '└')


def replace_last(string, char, replacement):
    return replacement.join(string.rsplit(char, 1))


LEVEL_COLORS = {
    logging.DEBUG: cyan,
    logging.WARNING: yellow,
    logging.ERROR: red,
    logging.CRITICAL: color('white', bg='red', bold=True),
}

LEVELS_PREFIX = {
    logging.INFO: cyan(INFO),
    logging.WARNING: yellow(WARNING),
}


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(pkg_resources.get_distribution('cada').version)
    ctx.exit()


@click.group(cls=FlaskGroup, create_app=create_app, context_settings=CONTEXT_SETTINGS,
             add_version_option=False, add_default_commands=False)
@click.option('--version', is_flag=True, callback=print_version, expose_value=False, is_eager=True)
def cli():
    '''CADA Management client'''


cli._loaded_plugin_commands = True  # Prevent extensions to register their commands
cli.add_command(shell_command)
cli.add_command(run_command, name='runserver')
cli.add_command(routes_command)


@cli.command()
@click.argument('patterns', nargs=-1)
@click.option('-r', '--reindex', 'full_reindex', is_flag=True,
              help='Trigger a full reindexation instead of indexing new advices')
def load(patterns, full_reindex):
    '''
    Load one or more CADA CSV files matching patterns
    '''
    header('Loading CSV files')
    for pattern in patterns:
        for filename in iglob(pattern):
            echo('Loading {}'.format(white(filename)))
            with open(filename) as f:
                reader = csv.reader(f)
                # Skip header
                reader.next()
                for idx, row in enumerate(reader, 1):
                    try:
                        advice = csv.from_row(row)
                        skipped = False
                        if not full_reindex:
                            index(advice)
                        echo('.' if idx % 50 else white(idx), nl=False)
                    except Exception:
                        echo(cyan('s') if idx % 50 else white('{0}(s)'.format(idx)), nl=False)
                        skipped = True
                if skipped:
                    echo(white('{}(s)'.format(idx)) if idx % 50 else '')
                else:
                    echo(white(idx) if idx % 50 else '')
                success('Processed {0} rows'.format(idx))
    if full_reindex:
        reindex()


@cli.command()
def reindex():
    '''Reindex all advices'''
    header('Reindexing all advices')
    echo('Deleting index {0}', white(es.index_name))
    if es.indices.exists(es.index_name):
        es.indices.delete(index=es.index_name)
    es.initialize()

    idx = 0
    for idx, advice in enumerate(Advice.objects, 1):
        index(advice)
        echo('.' if idx % 50 else white(idx), nl=False)
    echo(white(idx) if idx % 50 else '')
    es.indices.refresh(index=es.index_name)
    success('Indexed {0} advices', idx)


@cli.command()
@click.argument('path', default='static')
@click.option('-ni', '--no-input', is_flag=True, help="Disable input prompts")
def static(path, no_input):
    '''Compile and collect static files into path'''
    log = logging.getLogger('webassets')
    log.addHandler(logging.StreamHandler())
    log.setLevel(logging.DEBUG)

    cmdenv = CommandLineEnvironment(assets, log)
    cmdenv.build()

    if exists(path):
        warning('{0} directory already exists and will be {1}', white(path), white('erased'))
        if not no_input and not click.confirm('Are you sure'):
            exit_with_error()
        shutil.rmtree(path)

    echo('Copying assets into {0}', white(path))
    shutil.copytree(assets.directory, path)

    success('Done')


@cli.command()
def anon():
    '''Check for candidates to anonymization'''
    header(anon.__doc__)
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

        for idx, advice in enumerate(candidates, 1):
            writer.writerow(csv.to_anon_row(advice))
            echo('.' if idx % 50 else white(idx), nl=False)
        echo(white(idx) if idx % 50 else '')

    success('Total: {0} candidates', len(candidates))


@cli.command()
@click.argument('csvfile', default='fix.csv', type=click.File('r'))
def fix(csvfile):
    '''Apply a fix (ie. remove plain names)'''
    header('Apply fixes from {}', csvfile.name)
    bads = []
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
            echo('{0}: Replace {1} with {2}', white(id), white(source), white(dest))
            advice.subject = advice.subject.replace(source, dest)
            advice.content = advice.content.replace(source, dest)

        advice.save()
        index(advice)

    for id in bads:
        echo('{0}: Replacements length not matching', white(id))

    success('Done')
