#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.gis.geos import GEOSGeometry

from base.tests import FunctionalTestAfterLoginBase
from base.cache import cache_get
from place.models import UserPlace


class AfterLoginTaskTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(AfterLoginTaskTest, self).setUp()
        self.uplace = UserPlace(vd=self.vd)
        self.uplace.lonLat = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        self.uplace.save()

    def test_basic(self):
        from account.task_wrappers import AfterLoginTaskWrapper
        task = AfterLoginTaskWrapper()
        r = task.delay(self.vd_id)

        result = cache_get(self.vd, 'regions')
        self.assertNotEqual(result, None)
