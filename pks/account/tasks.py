#-*- coding: utf-8 -*-
from __future__ import unicode_literals


class AfterLoginTask(object):

    def run(self, vd_id):
        from account.models import VD
        vd = VD.objects.get(id=vd_id)

        # 캐싱 : uplaces, regions
        from place.libs import get_proper_uplaces_qs, compute_regions
        for uplace in get_proper_uplaces_qs(vd):
            placePost = uplace.placePost
            userPost = uplace.userPost
        compute_regions(vd)

        return True


class EmailTask(object):

    def run(self, to, title, msg):
        from base.utils import send_email
        r = send_email(to, title, msg)
        return r
