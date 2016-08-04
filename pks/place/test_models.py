#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from json import loads as json_loads
from urllib import unquote_plus

from base.tests import APITestBase
from place.models import Place, UserPlace, PostPiece
from account.models import VD, RealUser
from image.models import Image
from url.models import Url
from content.models import LegacyPlace, PhoneNumber, PlaceName, Address, PlaceNote, ImageNote
from base.utils import get_timestamp, BIT_ON_8_BYTE, BIT_ON_6_BYTE
from place.post import PostBase
from pks.settings import DISABLE_NO_FREE_API

class PlaceTest(APITestBase):

    def test_save_and_retreive(self):
        place = Place()
        place.save()
        saved = Place.objects.first()
        self.assertEqual(saved, place)

    def test_string_representation(self):
        place = Place()
        place.save()
        self.assertEqual(unicode(place), 'No named place object')
        placeName = PlaceName(content='능이향기')
        placeName.save()
        place.placeName = placeName
        place.save()
        self.assertEqual(unicode(place), '능이향기')

    def test_lonLat_column(self):
        place = Place()
        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        place.lonLat = point1
        place.save()
        saved = Place.objects.first()
        self.assertEqual(place.lonLat, point1)
        self.assertEqual(saved.lonLat, point1)

        point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        qs1 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs1), 0)
        qs2 = Place.objects.filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs2), 1)

    def test_placeName_column(self):
        place = Place()
        test_data = '능이향기'
        placeName = PlaceName(content=test_data)
        placeName.save()
        place.placeName = placeName
        place.save()
        saved = Place.objects.first()
        self.assertEqual(place.placeName, placeName)
        self.assertEqual(place.placeName.content, test_data)
        self.assertEqual(saved, place)
        self.assertEqual(saved.placeName, placeName)
        self.assertEqual(saved.placeName.content, test_data)
        self.assertEqual(placeName.places.first(), saved)
        self.assertEqual(Place.objects.filter(placeName=placeName).first(), saved)

    def test_get_or_create_smart(self):
        vd = VD.objects.create()
        test_data = 'http://place.kakao.com/places/15738374'
        lp, is_created = LegacyPlace.get_or_create_smart(test_data)
        pb = PostBase()
        pb.lps.append(lp)
        place, is_created = Place.get_or_create_smart(pb.pb_MAMMA, vd)
        placePost = place.placePost
        self.assertDictEqual(pb.pb_MAMMA.json, placePost.json)
        self.assertEqual(unicode(place), '방아깐')


class UserPlaceTest(APITestBase):

    def setUp(self):
        super(UserPlaceTest, self).setUp()
        self.place = Place()
        point = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        self.place.lonLat = point
        self.place.save()
        self.vd = VD()
        self.vd.save()

    def test_save_and_retreive(self):
        uplace = UserPlace(vd=self.vd)
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved, uplace)

    def test_id_property(self):
        uplace = UserPlace(vd=self.vd)
        self.assertEqual(uplace.id, None)
        timestamp = get_timestamp()
        uplace.save()
        self.assertNotEqual(uplace.id, None)
        self.assertAlmostEqual((int(uplace.id) >> 8*8) & BIT_ON_8_BYTE, timestamp, delta=1000)
        self.assertEqual((int(uplace.id) >> 2*8) & BIT_ON_6_BYTE, self.vd.id)
        saved = UserPlace.objects.first()
        self.assertEqual(saved, uplace)
        self.assertEqual(saved.id, uplace.id)

        # for timestamp property
        self.assertEqual(uplace.created, uplace.modified)
        self.assertEqual(saved.created, uplace.created)
        self.assertEqual(saved.modified, uplace.modified)
        self.assertAlmostEqual(uplace.created, timestamp, delta=1000)

    def test_id_property_with_timestamp(self):
        uplace = UserPlace(vd=self.vd)
        timestamp = get_timestamp()
        uplace.save(timestamp=timestamp)
        self.assertEqual((int(uplace.id) >> 8*8) & BIT_ON_8_BYTE, timestamp)
        self.assertEqual((int(uplace.id) >> 2*8) & BIT_ON_6_BYTE, self.vd.id)
        saved = UserPlace.objects.first()
        self.assertEqual(saved, uplace)
        self.assertEqual(saved.id, uplace.id)

    def test_id_property_with_no_vd(self):
        uplace = UserPlace()
        uplace.save()
        self.assertEqual((int(uplace.id) >> 2*8) & BIT_ON_6_BYTE, 0)

    def test_non_unique_vd_place(self):
        uplace = UserPlace(vd=self.vd, place=self.place)
        uplace.save()
        uplace2 = UserPlace(vd=self.vd, place=self.place)
        uplace2.save()
        self.assertNotEqual(uplace, uplace2)
        self.assertEqual(uplace.place, uplace2.place)

    def test_get_or_create(self):
        uplace, is_created = UserPlace.objects.get_or_create(vd=self.vd, place=self.place)
        self.assertEqual(is_created, True)
        uplace2, is_created = UserPlace.objects.get_or_create(vd=self.vd, place=self.place)
        self.assertEqual(is_created, False)
        self.assertEqual(uplace, uplace2)

    def test_created_modified(self):
        uplace = UserPlace(vd=self.vd, place=self.place)
        self.assertEqual(uplace.created, None)
        self.assertEqual(uplace.modified, None)
        uplace.save()
        t1 = uplace.modified
        self.assertNotEqual(t1, None)
        self.assertEqual(uplace.created, t1)
        self.assertAlmostEqual(t1, get_timestamp(), delta=1000)
        uplace.save()
        self.assertGreater(uplace.modified, t1)
        self.assertAlmostEqual(uplace.modified, t1, delta=1000)
        self.assertEqual(uplace.created, t1)
        t2 = get_timestamp()
        uplace.save(timestamp=t2)
        self.assertEqual(uplace.modified, t2)
        self.assertEqual(uplace.created, t1)

    def test_lonLat_column(self):
        uplace = UserPlace(vd=self.vd, place=self.place)
        uplace.save()
        point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        qs1 = UserPlace.objects.filter(place__lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs1), 0)
        qs2 = UserPlace.objects.filter(place__lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs2), 1)
        qs3 = UserPlace.objects.filter(lonLat__distance_lte=(point2, D(m=100)))
        self.assertEqual(len(qs3), 0)
        qs4 = UserPlace.objects.filter(vd_id=self.vd.id).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs4), 1)
        qs5 = UserPlace.objects.filter(vd_id=0).filter(lonLat__distance_lte=(point2, D(m=1000)))
        self.assertEqual(len(qs5), 0)

    def test_mask(self):
        uplace = UserPlace(vd=self.vd, place=self.place)
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_drop, False)
        self.assertEqual(saved.mask, 0 | 0)

        uplace.is_drop = True
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_drop, True)
        self.assertEqual(saved.mask, 0 | 1)
        uplace.is_drop = False
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_drop, False)
        self.assertEqual(saved.mask, 0 | 0)

        uplace.is_hard2placed = True
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_hard2placed, True)
        self.assertEqual(saved.mask, 0 | 2)
        uplace.is_hard2placed = False
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_hard2placed, False)
        self.assertEqual(saved.mask, 0 | 0)

        uplace.is_hurry2placed = True
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_hurry2placed, True)
        self.assertEqual(saved.mask, 0 | 4)
        uplace.is_hurry2placed = False
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_hurry2placed, False)
        self.assertEqual(saved.mask, 0 | 0)

        uplace.is_parent = True
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_parent, True)
        self.assertEqual(saved.mask, 0 | 8)
        uplace.is_parent = False
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_parent, False)
        self.assertEqual(saved.mask, 0 | 0)

        uplace.is_empty = True
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_empty, True)
        self.assertEqual(saved.mask, 0 | 16)
        uplace.is_empty = False
        uplace.save()
        saved = UserPlace.objects.first()
        self.assertEqual(saved.is_empty, False)
        self.assertEqual(saved.mask, 0 | 0)

    def test_get_from_post(self):
        vd_other = VD.objects.create()
        place_other = Place.objects.create()
        uplace1 = UserPlace.objects.create(vd=vd_other, place=self.place)
        uplace2 = UserPlace.objects.create(vd=self.vd, place=place_other)
        uplace3 = UserPlace.objects.create(vd=self.vd, place=self.place)
        pb = PostBase()
        pb.place_id = self.place.id
        ru = RealUser.objects.create(email='gulby@maukistudio.com')
        self.vd.realOwner = ru
        self.vd.save()
        vd_mine = VD.objects.create(realOwner=ru)
        uplace_check, is_created = UserPlace.get_or_create_smart(pb, vd_mine)
        self.assertNotEqual(uplace1, uplace_check)
        self.assertNotEqual(uplace2, uplace_check)
        self.assertEqual(uplace3, uplace_check)

    def test_origin(self):
        point = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        uplace = UserPlace.objects.create(vd=self.vd, lonLat=point)
        uplace.origin = point
        self.assertEqual(uplace.origin, point)
        self.assertEqual(UserPlace.objects.count(), 1)
        uplace2 = UserPlace.objects.first()
        self.assertEqual(uplace2.origin, None)

    def test_distance_from_origin(self):
        point = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        uplace = UserPlace.objects.create(vd=self.vd, lonLat=point)
        self.assertEqual(uplace.distance_from_origin, None)
        uplace.origin = point
        self.assertEqual(uplace.distance_from_origin, '0m')

        point2 = GEOSGeometry('POINT(127.107316 37.400998)', srid=4326)
        uplace.origin = point2
        self.assertEqual(uplace.distance_from_origin, '350m')

        point3 = GEOSGeometry('POINT(127.0 37.0)', srid=4326)
        uplace.origin = point3
        self.assertEqual(uplace.distance_from_origin, '45.3km')

    def test_aid(self):
        uplace = UserPlace.objects.create()
        aid = uplace.aid
        id = UserPlace.aid2id(aid)
        self.assertEqual(id, uplace.id)

    def test_shorten_url(self):
        place = Place.objects.create()
        uplace = UserPlace.objects.create(place=place)
        self.assertEqual(uplace.shorten_url, None)
        uplace.make_shorten_url()
        self.assertNotEqual(uplace.shorten_url, None)
        self.assertEqual(uplace.shorten_url.startswith('http://goo.gl/'), True)


class PostTest(APITestBase):

    def test_post(self):
        place = Place(); place.save()
        vd1 = VD(); vd1.save()
        uplace1 = UserPlace(vd=vd1, place=place)
        uplace1.save()
        point1 = GEOSGeometry('POINT(127 37)', srid=4326)
        name1, is_created = PlaceName.get_or_create_smart('능라')
        addr1, is_created = Address.get_or_create_smart('경기도 성남시 분당구 운중동 883-3')
        note11, is_created = PlaceNote.get_or_create_smart('분당 냉면 최고')
        note12, is_created = PlaceNote.get_or_create_smart('만두도 괜찮음')
        imgNote1, is_created = ImageNote.get_or_create_smart('냉면 사진')
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img1, is_created = Image.get_or_create_smart(img1_content)
        phone1, is_created = PhoneNumber.get_or_create_smart('010-5686-1613')

        vd2 = VD(); vd2.save()
        uplace2 = UserPlace(vd=vd2, place=place)
        uplace2.save()
        point2 = GEOSGeometry('POINT(127.1037430 37.3997320)', srid=4326)
        name2, is_created = PlaceName.get_or_create_smart('능라도')
        addr2, is_created = Address.get_or_create_smart('경기도 성남시 분당구 산운로32번길 12')
        note21, is_created = PlaceNote.get_or_create_smart('여기 가게 바로 옆으로 이전')
        note22, is_created = PlaceNote.get_or_create_smart('평양냉면 맛집')
        img21_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img22_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img21, is_created = Image.get_or_create_smart(img21_content)
        img22, is_created = Image.get_or_create_smart(img22_content)
        imgNote2, is_created = ImageNote.get_or_create_smart('만두 사진')
        url2, is_created = Url.get_or_create_smart('http://www.naver.com/')
        lp, is_created = LegacyPlace.get_or_create_smart('4ccffc63f6378cfaace1b1d6.4square')
        phone2, is_created = PhoneNumber.get_or_create_smart('010-5597-9245')

        json_userPost = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "addr2": {"uuid": "%s", "content": "%s"},
                "notes": [{"uuid": "%s", "content": "%s"}, {"uuid": "%s", "content": "%s"}],
                "images": [{"uuid": "%s", "content": "%s", "note": {"uuid": "%s", "content": "%s"}}],
                "urls": [],
                "lps": [],
                "phone": {"uuid": "%s", "content": "%s"}
            }
        ''' % (point1.x, point1.y, name1.uuid, name1.content, addr1.uuid, addr1.content,
               note12.uuid, note12.content, note11.uuid, note11.content, img1.uuid, img1.content, imgNote1.uuid, imgNote1.content,
               phone1.uuid, phone1.content,)
        json_placePost = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"uuid": "%s", "content": "%s"},
                "addr1": {"uuid": "%s", "content": "%s"},
                "addr2": {"uuid": "%s", "content": "%s"},
                "notes": [
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"},
                    {"uuid": "%s", "content": "%s"}
                ],
                "images": [
                    {"uuid": "%s", "content": "%s", "note": null},
                    {"uuid": "%s", "content": "%s", "note": {"uuid": "%s", "content": "%s"}},
                    {"uuid": "%s", "content": "%s", "note": {"uuid": "%s", "content": "%s"}}
                ],
                "urls": [{"uuid": "%s", "content": "%s"}],
                "lps": [{"uuid": "%s", "content": "%s"}],
                "phone": {"uuid": "%s", "content": "%s"}
            }
        ''' % (point2.x, point2.y, name2.uuid, name2.content,
               addr2.uuid, addr2.content, addr1.uuid, addr1.content,
               note22.uuid, note22.content, note21.uuid, note21.content, note12.uuid, note12.content, note11.uuid, note11.content,
               img22.uuid, img22.content, img21.uuid, img21.content, imgNote2.uuid, imgNote2.content, img1.uuid, img1.content, imgNote1.uuid, imgNote1.content,
               url2.uuid, url2.content, lp.uuid, lp.content, phone2.uuid, phone2.content,)
        pb1 = PostBase(json_userPost)
        pb2 = PostBase(json_placePost)
        self.assertEqual(PostPiece.objects.count(), 0)
        pp1 = PostPiece.create_smart(uplace1, pb1)
        self.assertEqual(PostPiece.objects.count(), 1)
        pp2 = PostPiece.create_smart(uplace2, pb2)
        pp3 = PostPiece.create_smart_4place(place, vd1, pb2, by_MAMMA=True)
        self.assertEqual(PostPiece.objects.count(), 3)

        want_userPost = json_loads(json_userPost)
        want_placePost = json_loads(json_placePost)

        self.assertNotIn('timestamp', uplace1.userPost.json['lonLat'])
        self.assertNotIn('timestamp', uplace1.userPost.json['name'])
        self.assertIn('timestamp', uplace1.userPost.json['notes'][0])
        self.assertNotIn('timestamp', uplace1.userPost.json['images'][0])
        self.assertIn('timestamp', uplace1.userPost.json['images'][0]['note'])

        self.assertNotIn('timestamp', uplace2.userPost.json['urls'][0])
        self.assertNotIn('timestamp', uplace2.userPost.json['lps'][0])
        timestamp = uplace1.userPost.json['notes'][0]['timestamp']
        self.assertAlmostEqual(get_timestamp(), timestamp, delta=1000)
        self.assertIn('summary', uplace1.userPost.json['images'][0])
        self.assertIn('phone', uplace1.userPost.json)
        self.assertNotEqual(uplace1.userPost.json['images'][0]['content'], None)

        self.assertIsSubsetOf(want_userPost, uplace1.userPost)
        self.assertIsNotSubsetOf(uplace1.userPost, want_userPost)

        self.assertIsSubsetOf(want_placePost, uplace1.place.placePost)
        self.assertIsNotSubsetOf(uplace1.place.placePost, want_placePost)
        uplace1._clearCache()
        p1 = uplace1.place.placePost
        uplace2._clearCache()
        p2 = uplace2.place.placePost
        place._clearCache()
        p3 = place.placePost
        self.assertDictEqual(p1.json, p3.json)
        self.assertDictEqual(p2.json, p3.json)

        pb12 = PostBase(json_userPost)
        pb12.update(pb1)
        self.assertNotEqual(pb12.json, pb1.json)
        pb12.normalize()
        self.assertEqual(pb12.json, pb1.json)

        pb13 = PostBase(json_userPost)
        pb13.update(pb1)
        pb13.update(pb1, add=False)
        pb_null = PostBase()
        self.assertEqual(pb13.json, pb_null.json)

        totalPost = place._totalPost
        self.assertIsSubsetOf(uplace1.place.placePost, totalPost)
        #self.assertIsSubsetOf(uplace1.userPost, totalPost)     # Note 에서 timestamp 를 제거해야...
        #self.assertIsSubsetOf(uplace2.userPost, totalPost)     # 상동
        #self.assertIsNotSubsetOf(totalPost, uplace1.place.placePost)   # userPost 를 하나 더 생성해야...

        # child/parent test
        uplace3 = UserPlace.objects.create(parent=uplace1)
        self.assertEqual(uplace3.parent, uplace1)
        self.assertNotEqual(uplace3.userPost, uplace1.userPost)
        self.assertEqual(uplace3.userPost.json, uplace1.userPost.json)
        uplace1._clearCache()
        uplace3._clearCache()
        pb3 = PostBase('{"notes": [{"content": "child"}]}')
        pp3 = PostPiece.create_smart(uplace3, pb3)
        self.assertNotEqual(uplace3.userPost, uplace1.userPost)
        self.assertNotEqual(uplace3.userPost.json, uplace1.userPost.json)

        place4 = Place.objects.create()
        uplace4 = UserPlace.objects.create(parent=uplace1, vd=vd1, place=place4)
        self.assertEqual(uplace4.parent, uplace1)
        self.assertNotEqual(uplace4.userPost, uplace1.userPost)
        self.assertEqual(uplace4.userPost.json, uplace1.userPost.json)
        uplace1._clearCache()
        uplace4._clearCache()
        pb3 = PostBase('{"notes": [{"content": "child"}]}')
        pp3 = PostPiece.create_smart(uplace4, pb3)
        self.assertNotEqual(uplace4.userPost, uplace1.userPost)
        self.assertNotEqual(uplace4.userPost.json, uplace1.userPost.json)


    def test_placed(self):
        vd = VD(); vd.save()
        pb_add = PostBase('{"urls": [{"content": "http://www.naver.com/"}]}')
        pb_place1 = PostBase('{"urls": [{"content": "http://place.kakao.com/places/15738374"}]}')
        pb_place2 = PostBase('{"urls": [{"content": "http://place.kakao.com/places/26455534"}]}')

        uplace, is_created = UserPlace.get_or_create_smart(pb_add, vd)
        self.assertEqual(uplace.place, None)

        pb_place1.uplace_uuid = uplace.uuid
        uplace, is_created = UserPlace.get_or_create_smart(pb_place1.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        self.assertEqual(uplace.lonLat, uplace.place.lonLat)
        place1 = uplace.place

        pb_place2.uplace_uuid = uplace.uuid
        pb_place2.place_id = place1.id
        uplace, is_created = UserPlace.get_or_create_smart(pb_place2.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        self.assertEqual(uplace.lonLat, uplace.place.lonLat)
        place2 = uplace.place

        self.assertNotEqual(place1, place2)
        self.assertNotEqual(place1.lonLat, place2.lonLat)

    def test_placed_by_name1(self):
        vd = VD(); vd.save()
        pb_add = PostBase('''{
            "lonLat": {"lon": 127.135037, "lat": 37.489283},
            "urls": [{"content": "http://www.naver.com/"}]
        }''')
        pb_name = PostBase('{"name": {"content": "바이키 문정점"}}')
        pb_place2 = PostBase('{"urls": [{"content": "http://place.kakao.com/places/26455534"}]}')

        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)
        uplace, is_created = UserPlace.get_or_create_smart(pb_add, vd)
        self.assertEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)

        pb_name.uplace_uuid = uplace.uuid
        uplace, is_created = UserPlace.get_or_create_smart(pb_name, vd)
        self.assertNotEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(PostPiece.objects.count(), 1)
        place1 = uplace.place
        self.assertEqual(place1.placePost.addr1, None)

        pb_place2.uplace_uuid = uplace.uuid
        uplace, is_created = UserPlace.get_or_create_smart(pb_place2.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        place2 = uplace.place
        self.assertEqual(place1, place2)
        self.assertEqual(Place.objects.count(), 1)
        self.assertNotEqual(place2.placePost.addr1, None)
        self.assertEqual(PostPiece.objects.count(), 2)

    def test_placed_by_name2(self):
        vd = VD(); vd.save()
        pb_add = PostBase('''{
            "urls": [{"content": "http://www.naver.com/"}]
        }''')
        pb_name = PostBase('{"name": {"content": "바이키 문정점"}}')
        pb_place2 = PostBase('{"urls": [{"content": "http://place.kakao.com/places/26455534"}]}')

        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)
        uplace, is_created = UserPlace.get_or_create_smart(pb_add, vd)
        self.assertEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)

        pb_place2.uplace_uuid = uplace.uuid
        uplace, is_created = UserPlace.get_or_create_smart(pb_place2.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        place2 = uplace.place
        self.assertEqual(Place.objects.count(), 1)
        self.assertNotEqual(place2.placePost.addr1, None)
        self.assertEqual(PostPiece.objects.count(), 1)

        pb_name.uplace_uuid = uplace.uuid
        uplace, is_created = UserPlace.get_or_create_smart(pb_name, vd)
        self.assertNotEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(PostPiece.objects.count(), 1)
        place1 = uplace.place
        self.assertEqual(place1, place2)
        self.assertNotEqual(place1.placePost.addr1, None)

    def test_image_by_url(self):
        '''
        pb = PostBase('{"urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=31130096"}]}')
        pb.load_additional_info()
        print(pb.images[0].content)
        self.assertIn(pb.images[0].content, [
            unquote_plus('https://ssl.map.naver.com/staticmap/image?version=1.1&crs=EPSG%3A4326&caller=og_map&center=127.0584149%2C37.3916387&level=11&scale=2&w=500&h=500&markers=type%2Cdefault2%2C127.0584149%2C37.3916387&baselayer=default'),
            'http://ldb.phinf.naver.net/20150902_90/1441122604108F2r99_JPEG/SUBMIT_1353817968111_31130096.jpg',
        ])
        '''

        pb = PostBase('{"urls": [{"content": "http://place.kakao.com/places/14720610"}]}')
        pb.load_additional_info()
        self.assertEqual(pb.images[0].content, unquote_plus(
            'http://img1.daumcdn.net/thumb/C300x300/?fname=http%3A%2F%2Fdn-rp-place.kakao.co.kr%2Fplace%2FoWaiTZmpy7%2FviOeK5KRQK7mEsAHlckFgK%2FapreqCwxgnM_l.jpg'
        ))

        pb = PostBase('{"urls": [{"content": "http://m.blog.naver.com/mardukas/220671562152"}]}')
        pb.load_additional_info()
        self.assertEqual(pb.images[0].content, 'http://blogthumb2.naver.net/20160401_292/mardukas_1459496453119PGXjg_JPEG/DSC03071.JPG?type=w2')


class PostPieceTest(APITestBase):

    def setUp(self):
        super(PostPieceTest, self).setUp()
        self.place = Place()
        self.place.save()
        self.uplace = UserPlace()
        self.uplace.save()
        self.vd = VD()
        self.vd.save()

        self.image, is_created = Image.get_or_create_smart('http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg')
        self.url, is_created = Url.get_or_create_smart('http://www.naver.com/')

        self.lp, is_created = LegacyPlace.get_or_create_smart('4ccffc63f6378cfaace1b1d6.4square')
        self.addr, is_created = Address.get_or_create_smart('경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.phone, is_created = PhoneNumber.get_or_create_smart('010-5597-9245')

    def test_save_and_retreive(self):
        pp = PostPiece()
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(saved, pp)

    def test_id_property(self):
        pp = PostPiece(vd=self.vd)
        self.assertEqual(pp.id, None)
        timestamp = get_timestamp()
        pp.save()
        self.assertNotEqual(pp.id, None)
        self.assertAlmostEqual((int(pp.id) >> 8*8) & BIT_ON_8_BYTE, timestamp, delta=1000)
        self.assertEqual((int(pp.id) >> 2*8) & BIT_ON_6_BYTE, self.vd.id)
        saved = PostPiece.objects.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.id, pp.id)

        # for timestamp property
        self.assertEqual(saved.timestamp, pp.timestamp)
        self.assertAlmostEqual(pp.timestamp, timestamp, delta=1000)

    def test_id_property_with_timestamp(self):
        pp = PostPiece(vd=self.vd)
        timestamp = get_timestamp()
        pp.save(timestamp=timestamp)
        self.assertEqual((int(pp.id) >> 8*8) & BIT_ON_8_BYTE, timestamp)
        self.assertEqual((int(pp.id) >> 2*8) & BIT_ON_6_BYTE, self.vd.id)
        saved = PostPiece.objects.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.id, pp.id)

    def test_id_property_with_no_vd(self):
        pp = PostPiece()
        pp.save()
        self.assertEqual((int(pp.id) >> 2*8) & BIT_ON_6_BYTE, 0)

    def test_uplace_property(self):
        pp = PostPiece()
        pp.uplace = self.uplace
        pp.save()
        saved = self.uplace.pps.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.uplace, pp.uplace)
        self.assertEqual(saved.place, None)

    def test_place_property(self):
        pp = PostPiece()
        pp.place = self.place
        pp.save()
        saved = self.place.pps.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.place, pp.place)

        self.uplace.place = self.place
        self.uplace.save()
        pp2 = PostPiece()
        pp2.uplace = self.uplace
        self.assertEqual(pp2.place, None)
        pp2.save()
        self.assertEqual(pp2.place, self.place)

    def test_vd_property(self):
        pp = PostPiece()
        pp.vd = self.vd
        pp.save()
        saved = self.vd.pps.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.vd, pp.vd)

    def test_data_property(self):
        # TODO : json 에 대한 query 테스트 추가
        pp = PostPiece()
        json_add = json_loads('''
            {
                "lonLat": {"lon": 127.1037430, "lat": 37.3997320},
                "images": [{"content": "http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg"}],
                "addr1": {"content": "경기도 성남시 분당구 판교로 256번길 25"},
                "addr2": {"content": "경기도 성남시 분당구 삼평동 631"},
                "addr3": {"content": "경기도 성남시 분당구 삼평동"},
                "urls": [{"content": "http://place.kakao.com/places/15738374"}]
            }
        ''')
        pp.data = json_add
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(json_add, pp.data)
        self.assertEqual(json_add, saved.data)

        pp2 = PostPiece()
        pb = PostBase(json_add)
        pp2.pb = pb
        pp2.save()
        saved = PostPiece.objects.order_by('-id').first()
        self.assertEqual(pp2, saved)
        self.assertDictEqual(pp2.pb.json, saved.pb.json)
        self.assertDictEqual(pp2.pb.cjson, saved.pb.cjson)
        self.assertDictEqual(pb.json, saved.pb.json)
        self.assertDictEqual(pb.cjson, saved.pb.cjson)

    def test_mask(self):
        pp = PostPiece()
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(saved.is_remove, False)
        self.assertEqual(saved.is_add, True)
        self.assertEqual(saved.by_MAMMA, False)
        self.assertEqual(saved.is_drop, False)
        self.assertEqual(saved.mask, 0 | 0)

        pp.is_remove = True
        pp.by_MAMMA = False
        pp.is_drop = True
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(saved.is_remove, True)
        self.assertEqual(saved.is_add, False)
        self.assertEqual(saved.by_MAMMA, False)
        self.assertEqual(saved.is_drop, True)
        self.assertEqual(saved.mask, 4 | 0 | 1)

        pp.is_remove = False
        pp.by_MAMMA = True
        pp.is_drop = False
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(saved.is_remove, False)
        self.assertEqual(saved.is_add, True)
        self.assertEqual(saved.by_MAMMA, True)
        self.assertEqual(saved.is_drop, False)
        self.assertEqual(saved.mask, 0 | 2 | 0)

        pp.by_MAMMA = False
        pp.is_drop = True
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(saved.is_remove, False)
        self.assertEqual(saved.is_add, True)
        self.assertEqual(saved.by_MAMMA, False)
        self.assertEqual(saved.is_drop, True)
        self.assertEqual(saved.mask, 4 | 0 | 0)


class PostBaseTest(APITestBase):

    def test_setUp_with_None(self):
        pb = PostBase()
        json = pb.json
        pb2 = PostBase(json)
        self.assertDictEqual(json, pb2.json)

    def test_setUp_with_str(self):
        json_add = '''
            {
                "lonLat": {"lon": 127.1037430, "lat": 37.3997320},
                "images": [{"content": "http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg"}],
                "addr1": {"content": "경기도 성남시 분당구 판교로 256번길 25"},
                "addr2": {"content": "경기도 성남시 분당구 삼평동 631"},
                "urls": [{"content": "http://place.kakao.com/places/15738374"}]
            }
        '''
        pb = PostBase(json_add)
        json = pb.json
        pb2 = PostBase(json)
        self.assertDictEqual(json, pb2.json)
        self.assertIsSubsetOf(json_loads(json_add), json)
        self.printJson(pb.pb_MAMMA)

