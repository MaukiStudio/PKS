#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task


class PlaceTaskWrapper(Task):

    def run(self, place_id):
        from place.tasks import PlaceTask
        task = PlaceTask()
        return task.run(place_id)
