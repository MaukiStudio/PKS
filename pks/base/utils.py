#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from delorean import Delorean


# bit mask
BIT_ON_8_BYTE = int('0xFFFFFFFFFFFFFFFF', 16)
BIT_ON_6_BYTE = int('0x0000FFFFFFFFFFFF', 16)


class HashCollisionError(NotImplementedError):
    pass


def get_timestamp():
    return int(round(Delorean().epoch*1000))

