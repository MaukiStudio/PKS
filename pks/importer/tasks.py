#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task

from account.models import VD


class ImagesImporter(Task):
    def run(self, imp):
        vd_id = imp.publisher.vd.id
        vd = VD.objects.get(id=vd_id)
        return vd.deviceName

