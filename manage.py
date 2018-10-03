#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from cada.commands import cli

if __name__ == "__main__":
    os.environ['FLASK_ENV'] = 'development'
    cli()
