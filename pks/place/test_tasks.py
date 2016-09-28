#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.gis.geos import GEOSGeometry

from base.tests import APITestBase
from pks.settings import WORK_ENVIRONMENT
from account.models import VD
from place.models import Place, PlaceName, UserPlace
from place.task_wrappers import PlaceTaskWrapper


class PlaceTaskTest(APITestBase):

    def test_task(self):
        if WORK_ENVIRONMENT: return
        placeName, is_created = PlaceName.get_or_create_smart('미사강변도시 베라체')
        lonLat = GEOSGeometry('POINT(127.1786679 37.5723805)', srid=4326)
        place = Place.objects.create(lonLat=lonLat, placeName=placeName)
        vd = VD.objects.create()
        uplace = UserPlace.objects.create(vd=vd, place=place)
        self.assertEqual(place.placePost.addr, None)
        self.assertEqual(place.placePost.phone, None)
        task = PlaceTaskWrapper()
        task.delay(place.id)
        place = Place.objects.get(id=place.id)
        place._clearCache()
        self.assertEqual(place.placePost.addr.content, 'South Korea, Gyeonggi-do, Hanam-si, Pungsan-dong, 풍산로 270')
        self.assertEqual(place.placePost.phone.content, '+82317961917')

    def test_task_no_image(self):
        placeName, is_created = PlaceName.get_or_create_smart('Calle Nueva')
        lonLat = GEOSGeometry('POINT(-5.166208 36.741447)', srid=4326)
        place = Place.objects.create(lonLat=lonLat, placeName=placeName)
        vd = VD.objects.create()
        uplace = UserPlace.objects.create(vd=vd, place=place)
        task = PlaceTaskWrapper()
        task.delay(place.id)
        place = Place.objects.get(id=place.id)
        self.assertEqual(place.lps.count(), 1)
        place.lps.first().access_force()
        place.lps.first().summarize_force()
