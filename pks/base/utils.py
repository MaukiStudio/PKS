#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from delorean import Delorean


def get_timestamp():
    return int(round(Delorean().epoch*1000))
