#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from place.models import UserPlace
from place.libs import compute_regions


class RegionTest(APITestBase):
    def setUp(self):
        super(RegionTest, self).setUp()
        self.uplaces = list()
        with open('place/samples/lonLat.txt') as f:
            for line in f.readlines():
                uplace = UserPlace()
                uplace.lonLat = GEOSGeometry(line)
                uplace.value = uplace.lonLat
                uplace.timestamp = 1
                self.uplaces.append(uplace)

    def __skip__test_compute_regions(self):
        result = compute_regions(uplaces=self.uplaces)
        self.fail()
