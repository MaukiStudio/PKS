#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task


class ImporterTaskWrapper(Task):

    def run(self, imp_id):
        from importer.tasks import ImporterTask
        task = ImporterTask()
        return task.run(imp_id)


class ProxyTaskWrapper(Task):

    def run(self, proxy_id):
        from importer.tasks import ProxyTask
        task = ProxyTask()
        return task.run(proxy_id)
