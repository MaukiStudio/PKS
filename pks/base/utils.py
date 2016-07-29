#-*- coding: utf-8 -*-
from __future__ import unicode_literals


# bit mask
BIT_ON_8_BYTE = int('0xFFFFFFFFFFFFFFFF', 16)
BIT_ON_6_BYTE = int('0x0000FFFFFFFFFFFF', 16)


class HashCollisionError(NotImplementedError):
    pass


_prev_timestamp = 0
def get_timestamp():
    from delorean import Delorean
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
    return l


def get_uuid_from_ts_vd(timestamp, vd_id):
    from uuid import UUID
    from random import randrange
    hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]     # 끝에 붙는 L 을 떼내기 위해 -1
    return UUID(hstr.rjust(32, b'0'))


def call(func):
    ts_start = get_timestamp()
    if not func():
        raise NotImplementedError
    ts_end = get_timestamp()
    func_name = str(func).split(' ')[2]
    #print('%s(): %0.1f' % (func_name, (ts_end - ts_start)/1000.0))


def send_email(to, title, msg):
    from requests import post as requests_post
    from rest_framework import status
    to_name = to.split('@')[0]
    data = {'from': 'PlaceKoob <gulby@maukistudio.com>',
            'to': '%s <%s>' % (to_name, to),
            'subject': title,
            'text': msg}
    r = requests_post(
        'https://api.mailgun.net/v3/maukistudio.com/messages',
        auth=('api', 'key-1b25db28c7b404487efb45adc1aaf953'),
        data=data)
    return r.status_code == status.HTTP_200_OK


def convert_wgs84_to_daumurl(point):
    import pyproj
    wgs84 = pyproj.Proj('+init=EPSG:4326')
    daum = pyproj.Proj('+init=EPSG:5181')
    x, y = pyproj.transform(wgs84, daum, point.x, point.y)
    return (x/0.4, y/0.4)
