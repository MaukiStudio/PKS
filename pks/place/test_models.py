#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from json import loads as json_loads
from django.contrib.gis.geos import GEOSGeometry
from time import sleep
from django.db import IntegrityError

from base.tests import APITestBase
from place import models
from account.models import VD
from image.models import Image
from url.models import Url
from content.models import LegacyPlace, ShortText
from base.utils import get_timestamp

BIT_ON_8_BYTE = int('0xFFFFFFFFFFFFFFFF', 16)
BIT_ON_6_BYTE = int('0x0000FFFFFFFFFFFF', 16)


class PlaceTest(APITestBase):

    def test_save_and_retreive(self):
        place = models.Place()
        place.save()
        saved = models.Place.objects.first()
        self.assertEqual(saved, place)

    def test_post(self):
        place = models.Place()
        place.save()

        vd1 = VD(); vd1.save()
        point1 = GEOSGeometry('POINT(127 37)')
        name1 = ShortText(content='능라'); name1.save()
        addr1 = ShortText(content='경기도 성남시 분당구 운중동 883-3'); addr1.save()
        note11 = ShortText(content='분당 냉면 최고'); note11.save()
        note12 = ShortText(content='만두도 괜찮음'); note12.save()
        imgNote1 = ShortText(content='냉면 사진'); imgNote1.save()
        img1 = Image(file=self.uploadImage('test.jpg')); img1.save()

        # 현재 위치 저장
        pc11 = models.PlaceContent(vd=vd1, place=place, lonLat=point1, image=img1, stxt=addr1, stxt_type=models.STXT_TYPE_POS_DESC); pc11.save(); sleep(0.001)
        pc12 = models.PlaceContent(vd=vd1, place=place, lonLat=point1, image=img1, stxt=note11, stxt_type=models.STXT_TYPE_PLACE_NOTE); pc12.save(); sleep(0.001)
        # 이름 지정
        pc13 = models.PlaceContent(vd=vd1, place=place, stxt=name1, stxt_type=models.STXT_TYPE_PLACE_NAME); pc13.save(); sleep(0.001)
        # 노트 추가
        pc14 = models.PlaceContent(vd=vd1, place=place, stxt=note12, stxt_type=models.STXT_TYPE_PLACE_NOTE); pc14.save(); sleep(0.001)
        # 이미지노트 추가
        pc15 = models.PlaceContent(vd=vd1, place=place, image=img1, stxt=imgNote1, stxt_type=models.STXT_TYPE_IMAGE_NOTE); pc15.save(); sleep(0.001)

        vd2 = VD(); vd2.save()
        point2 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        name2 = ShortText(content='능라도'); name2.save()
        addr2 = ShortText(content='경기도 성남시 분당구 산운로32번길 12'); addr2.save()
        note21 = ShortText(content='여기 가게 바로 옆으로 이전'); note21.save()
        note22 = ShortText(content='평양냉면 맛집'); note22.save()
        img21 = Image(file=self.uploadImage('no_exif_test.jpg')); img21.save()
        img22 = Image(file=self.uploadImage('test_480.jpg')); img22.save()
        imgNote2 = ShortText(content='만두 사진'); imgNote2.save()
        url2 = Url(content='http://maukistudio.com/'); url2.save()
        lp = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp.save();

        # URL 저장
        pc21 = models.PlaceContent(vd=vd2, place=place, url=url2, stxt=note21, stxt_type=models.STXT_TYPE_PLACE_NOTE); pc21.save(); sleep(0.001)
        # 이름 지정
        pc22 = models.PlaceContent(vd=vd2, place=place, stxt=name2, stxt_type=models.STXT_TYPE_PLACE_NAME); pc22.save(); sleep(0.001)
        # 주소 지정
        pc23 = models.PlaceContent(vd=vd2, place=place, stxt=addr2, stxt_type=models.STXT_TYPE_POS_DESC); pc23.save(); sleep(0.001)
        # 이미지, 노트 추가
        pc24 = models.PlaceContent(vd=vd2, place=place, lonLat=point2, image=img21, stxt=note22, stxt_type=models.STXT_TYPE_PLACE_NOTE); pc24.save(); sleep(0.001)
        # 장소화
        pc25 = models.PlaceContent(vd=vd2, place=place, lp=lp); pc25.save(); sleep(0.001)
        # 이미지노트 추가
        pc26 = models.PlaceContent(vd=vd2, place=place, image=img21, stxt=imgNote2, stxt_type=models.STXT_TYPE_IMAGE_NOTE); pc26.save(); sleep(0.001)
        # (노트없는) 이미지 추가
        pc27 = models.PlaceContent(vd=vd2, place=place, image=img22); pc27.save(); sleep(0.001)

        json_userPost = '''
            {
                "place_id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "posDesc": {"uuid": "%s", "content": "%s"},
                "notes": [{"uuid": "%s", "content": "%s"}, {"uuid": "%s", "content": "%s"}],
                "images": [{"uuid": "%s", "content": null, "note": {"uuid": "%s", "content": "%s"}}],
                "urls": [],
                "lps": []
            }
        ''' % (place.id, point1.x, point1.y, name1.uuid, name1.content, addr1.uuid, addr1.content,
               note12.uuid, note12.content, note11.uuid, note11.content, img1.uuid, imgNote1.uuid, imgNote1.content,)
        json_placePost = '''
            {
                "place_id": %d,
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "posDesc": {"uuid": "%s", "content": "%s"},
                "notes": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "images": [
                    {"uuid": "%s", "content": null, "note": null},
                    {"uuid": "%s", "content": null, "note": {"uuid": "%s", "content": "%s"}},
                    {"uuid": "%s", "content": null, "note": {"uuid": "%s", "content": "%s"}}
                ],
                "urls": [{"uuid": "%s", "content": "%s"}],
                "lps": [{"uuid": "%s", "content": "%s"}]
            }
        ''' % (place.id, point2.x, point2.y, name2.uuid, name2.content, addr2.uuid, addr2.content,
               note22.uuid, note22.content, note21.uuid, note21.content, note12.uuid, note12.content, note11.uuid, note11.content,
               img22.uuid, img21.uuid, imgNote2.uuid, imgNote2.content, img1.uuid, imgNote1.uuid, imgNote1.content,
               url2.uuid, url2.content, lp.uuid, lp.content,)
        want_userPost = json_loads(json_userPost)
        want_placePost = json_loads(json_placePost)
        place.computePost([vd1.id])

        self.assertDictEqual(place.userPost, want_userPost)
        self.assertDictEqual(place.placePost, want_placePost)

        # UserPlaceTest 에서 구현되어야 할 사항이나, 편의상 여기에 구현
        post, created = models.UserPlace.objects.get_or_create(vd=vd1, place=place)
        self.assertEqual(created, True)
        self.assertEqual(post.userPost, place.userPost)


class PlaceContentTest(APITestBase):

    def setUp(self):
        self.place = models.Place()
        self.place.save()
        self.vd = VD()
        self.vd.save()

        self.image = Image()
        self.image.file = self.uploadImage('test.jpg')
        self.image.save()
        self.url = Url(content='http://maukistudio.com/')
        self.url.save()

        self.lp = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square')
        self.lp.save()
        self.stxt = ShortText(content='경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.stxt.save()

    def test_save_and_retreive(self):
        pc = models.PlaceContent()
        pc.save()
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)

    def test_id_property(self):
        pc = models.PlaceContent(vd=self.vd)
        self.assertEqual(pc.id, None)
        timestamp = get_timestamp()
        pc.save()
        self.assertNotEqual(pc.id, None)
        self.assertAlmostEqual((int(pc.id) >> 8*8) & BIT_ON_8_BYTE, timestamp, delta=1000)
        self.assertEqual((int(pc.id) >> 2*8) & BIT_ON_6_BYTE, self.vd.id)
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)
        self.assertEqual(saved.id, pc.id)

    def test_id_property_with_timestamp(self):
        pc = models.PlaceContent(vd=self.vd)
        timestamp = get_timestamp()
        pc.save(timestamp=timestamp)
        self.assertEqual((int(pc.id) >> 8*8) & BIT_ON_8_BYTE, timestamp)
        self.assertEqual((int(pc.id) >> 2*8) & BIT_ON_6_BYTE, self.vd.id)
        saved = models.PlaceContent.objects.first()
        self.assertEqual(saved, pc)
        self.assertEqual(saved.id, pc.id)

    def test_id_property_with_no_vd(self):
        pc = models.PlaceContent()
        pc.save()
        self.assertEqual((int(pc.id) >> 2*8) & BIT_ON_6_BYTE, 0)

    def test_place_property(self):
        pc = models.PlaceContent()
        pc.place = self.place
        pc.save()
        saved = self.place.pcs.get(id=pc.id)
        self.assertEqual(saved, pc)

    def test_vd_property(self):
        pc = models.PlaceContent()
        pc.vd = self.vd
        pc.save()
        saved = self.vd.pcs.get(id=pc.id)
        self.assertEqual(saved, pc)

    def test_lonLat_property(self):
        pc = models.PlaceContent()
        point = GEOSGeometry('POINT(127.1037430 37.3997320)')
        pc.lonLat = point
        pc.save()
        saved = models.PlaceContent.objects.first()
        self.assertEqual(point, saved.lonLat)

    def test_image_property(self):
        pc = models.PlaceContent()
        pc.image = self.image
        pc.save()
        saved = self.image.pcs.get(id=pc.id)
        self.assertEqual(pc.image, self.image)
        self.assertEqual(pc.lonLat, None)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.image, self.image)
        self.assertEqual(saved.lonLat, None)

    def test_url_property(self):
        pc = models.PlaceContent()
        pc.url = self.url
        pc.save()
        saved = self.url.pcs.get(id=pc.id)
        self.assertEqual(pc.url, self.url)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.url, self.url)

    def test_lp_property(self):
        pc = models.PlaceContent()
        pc.lp = self.lp
        pc.save()
        saved = self.lp.pcs.get(id=pc.id)
        self.assertEqual(pc.lp, self.lp)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.lp, self.lp)

    def test_stxt_property(self):
        pc = models.PlaceContent()
        pc.stxt = self.stxt
        pc.stxt_type = models.STXT_TYPE_PLACE_NOTE
        pc.save()
        saved = self.stxt.pcs.get(id=pc.id)
        self.assertEqual(pc.stxt, self.stxt)
        self.assertEqual(saved, pc)
        self.assertEqual(saved.stxt, self.stxt)
        self.assertEqual(saved.stxt_type, models.STXT_TYPE_PLACE_NOTE)


class UserPlaceTest(APITestBase):

    def setUp(self):
        self.place = models.Place()
        self.place.save()
        self.vd = VD()
        self.vd.save()

    def test_save_and_retreive(self):
        post = models.UserPlace(vd=self.vd, place=self.place)
        post.save()
        saved = models.UserPlace.objects.first()
        self.assertEqual(saved, post)

    def test_unique_vd_place(self):
        post = models.UserPlace(vd=self.vd, place=self.place)
        post.save()
        post2 = models.UserPlace(vd=self.vd, place=self.place)
        with self.assertRaises(IntegrityError):
            post2.save()

    def test_get_or_create(self):
        post, created = models.UserPlace.objects.get_or_create(vd=self.vd, place=self.place)
        self.assertEqual(created, True)
        post2, created = models.UserPlace.objects.get_or_create(vd=self.vd, place=self.place)
        self.assertEqual(created, False)
        self.assertEqual(post, post2)

    def test_userPost(self):
        # 편의상 PlaceTest.test_post() 에 구현
        pass
