#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task
from pks.settings import WORK_ENVIRONMENT


class AfterLoginTaskWrapper(Task):
    def run(self, vd_id):
        from account.tasks import AfterLoginTask
        task = AfterLoginTask()
        return task.run(vd_id)


class EmailTaskWrapper(Task):
    def run(self, to, title, msg):
        if WORK_ENVIRONMENT: return True
        if to.split('@')[1] == 'maukistudio.com':
            return True
        from account.tasks import EmailTask
        task = EmailTask()
        return task.run(to, title, msg)
