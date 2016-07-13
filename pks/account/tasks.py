#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.cache import cache_set


class TaskAfterLogin(object):

    def run(self, vd_id):
        from account.models import VD
        vd = VD.objects.get(id=vd_id)

        # regions API 결과 캐싱
        from place.libs import compute_regions
        cache_set(vd, 'regions', None, compute_regions, None, vd)

        return True
    