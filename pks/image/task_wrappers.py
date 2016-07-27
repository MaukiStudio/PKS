#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task


class AfterRawFileCreationTaskWrapper(Task):

    def run(self, rf_id):
        from image.tasks import AfterRawFileCreationTask
        task = AfterRawFileCreationTask()
        return task.run(rf_id)


class AfterImageCreationTaskWrapper(Task):

    def run(self, img_id):
        from image.tasks import AfterImageCreationTask
        task = AfterImageCreationTask()
        return task.run(img_id)

