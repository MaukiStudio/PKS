#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from base.tests import FunctionalTestAfterLoginBase
from base.cache import cache_get_or_create


class TaskAfterLoginTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(TaskAfterLoginTest, self).setUp()

    def test_basic(self):
        from account.task_wrappers import TaskAfterLoginWrapper
        task = TaskAfterLoginWrapper()
        r = task.delay(self.vd_id)

        from place.libs import compute_regions
        result, is_created = cache_get_or_create(self.vd, 'regions', None, compute_regions, None, self.vd)
        self.assertEqual(is_created, False)