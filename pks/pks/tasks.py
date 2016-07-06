#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from pks.celery import app
from time import sleep

# Test for DJANGO_SETTINGS_MODULE
from image.models import Image


@app.task
def for_unit_test(x, y):
    sleep(0.1)
    return x + y
