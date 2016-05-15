#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task
from importer.tasks import ImporterTask, ProxyTask


class ImporterTaskWrapper(Task):

    def run(self, imp_id):
        task = ImporterTask()
        return task.run(imp_id)


class ProxyTaskWrapper(Task):

    def run(self, proxy_id):
        task = ProxyTask()
        return task.run(proxy_id)
