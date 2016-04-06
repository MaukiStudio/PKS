#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from delorean import Delorean


class HashCollisionError(NotImplementedError):
    pass


def get_timestamp():
    return int(round(Delorean().epoch*1000))

