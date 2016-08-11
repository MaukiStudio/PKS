#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from celery import Celery


app = Celery(
    'pks',
    broker='amqp://guest:guest@localhost:5672//',
    backend='rpc://',
    include=[
        'pks.tasks',
        'importer.task_wrappers',
        'account.task_wrappers',
        'image.task_wrappers',
        'place.task_wrappers',
    ],
)

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()
