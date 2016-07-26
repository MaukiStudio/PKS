#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task


class AfterImageCreationTaskWrapper(Task):

    def run(self, img_id):
        from image.tasks import AfterImageCreationTask
        task = AfterImageCreationTask()
        return task.run(img_id)

