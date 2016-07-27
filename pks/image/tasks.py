#-*- coding: utf-8 -*-
from __future__ import unicode_literals


class AfterRawFileCreationTask(object):

    def run(self, rf_id):
        from image.models import RawFile
        rf = RawFile.objects.get(id=rf_id)
        return rf.task()


class AfterImageCreationTask(object):

    def run(self, img_id):
        from image.models import Image
        img = Image.objects.get(id=img_id)
        return img.task()
