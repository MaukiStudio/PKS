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


def is_valid_json_item(item_name, json):
    if item_name in json and json[item_name]:
        item_json = json[item_name]
        if 'content' in item_json:
            return item_json['content'] != 'None'
        else:
            return True
    return False


def remove_list(l1, l2):
    return [e for e in l1 if e not in l2]


def remove_duplicates(l):
    if l:
        return reduce(lambda a, b: b[0] in a and a or a + b, [[i] for i in l])
    return None
