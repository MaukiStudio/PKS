#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from delorean import Delorean


# bit mask
BIT_ON_8_BYTE = int('0xFFFFFFFFFFFFFFFF', 16)
BIT_ON_6_BYTE = int('0x0000FFFFFFFFFFFF', 16)


class HashCollisionError(NotImplementedError):
    pass


_prev_timestamp = int(round(Delorean().epoch*1000))
def get_timestamp():
    global _prev_timestamp
    _timestamp = int(round(Delorean().epoch*1000))
    if _prev_timestamp >= _timestamp:
        _timestamp = _prev_timestamp + 1
    _prev_timestamp = _timestamp
    return _timestamp
