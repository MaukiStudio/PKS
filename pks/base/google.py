#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from random import randrange

API_KEYS = ['AIzaSyCqc2GQDrA1J2l8reCYcKp9RymDumyreSg',
            'AIzaSyBUox6pBmiFtv0PA-KukrOHRcW4_HO2xyw', ]


def get_api_key(idx=None):
    cnt = len(API_KEYS)
    if idx is None:
        idx = randrange(0, cnt)
    return API_KEYS[idx]
