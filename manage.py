# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from cada import app
from cada.commands import manager

if __name__ == "__main__":
    app.config['ASSETS_DEBUG'] = True
    manager.run()
