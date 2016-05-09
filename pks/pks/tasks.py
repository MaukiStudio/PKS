#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from pks.celery import app
from time import sleep


@app.task
def for_unit_test(x, y):
    sleep(0.5)
    return x + y
