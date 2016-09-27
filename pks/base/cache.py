#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.cache import cache as django_cache

TTL_DEFAULT = 10*60
TTL_MIN = 1*60

def get_value_key(vd, name):
    return 'v%s_%s' % (vd.id, name)

def get_lock_key(vd, name):
    return 'l%s_%s' % (vd.id, name)

def init_ttl(ttl):
    if not ttl:
        ttl = TTL_DEFAULT
    elif ttl < TTL_MIN:
        ttl = TTL_MIN
    return ttl


def cache_get(vd, name):
    value_key = get_value_key(vd, name)
    value = django_cache.get(value_key)
    return value


def cache_set(vd, name, ttl, func, *args):
    ttl = init_ttl(ttl)
    value_key = get_value_key(vd, name)
    lock_key = get_lock_key(vd, name)

    with django_cache.lock(lock_key):
        old_ttl = django_cache.ttl(value_key)
        if old_ttl <= 0 or ttl - old_ttl >= TTL_MIN:
            value = func(*args)
            if value is not None:
                django_cache.set(value_key, value, ttl)
        else:
            value = django_cache.get(value_key)

    return value


# 중첩 lock 이 지원되지 않음. 따라서 cache_set() 을 이용한 구현은 위험
def cache_get_or_create(vd, name, ttl, func, *args):
    ttl = init_ttl(ttl)
    value_key = get_value_key(vd, name)
    lock_key = get_lock_key(vd, name)
    value = django_cache.get(value_key)
    is_created = False

    if value is None:
        with django_cache.lock(lock_key):
            # 찰나의 사이에 lock 이 걸릴 수 있으므로 lock 을 건후 ttl 을 check할 필요가 있다
            old_ttl = django_cache.ttl(value_key)
            if old_ttl <= 0:
                value = func(*args)
                if value is not None:
                    django_cache.set(value_key, value, ttl)
                    is_created = True
                else:
                    is_created = False

    return value, is_created


def cache_expire(vd, name, ttl=0):
    value_key = get_value_key(vd, name)
    django_cache.expire(value_key, timeout=ttl)


def cache_expire_ru(vd, name, ttl=0):
    if vd.realOwner:
        for vd in vd.realOwner.vds.all():
            cache_expire(vd, name, ttl)
    else:
        cache_expire(vd, name, ttl)


def cache_clear(vd):
    searcher = get_value_key(vd, '*')
    for value_key in django_cache.keys(searcher):
        django_cache.expire(value_key, timeout=0)


def cache_clear_ru(ru):
    for vd in ru.vds.all():
        cache_clear(vd)
