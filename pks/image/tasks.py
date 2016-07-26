#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from pks.settings import WORK_ENVIRONMENT


class AfterImageCreationTask(object):

    def run(self, img_id):
        from image.models import Image
        img = Image.objects.get(id=img_id)
        if img.rf:
            img.rf.task()
        r = img.task()
        return r
