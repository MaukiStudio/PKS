#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from json import loads as json_loads

from base.tests import APITestBase, isSubsetOf
from place.models import Place, UserPlace, PostPiece
from account.models import VD
from image.models import Image
from url.models import Url
from content.models import LegacyPlace, PhoneNumber, PlaceName, Address, PlaceNote, ImageNote
from base.utils import get_timestamp, BIT_ON_8_BYTE, BIT_ON_6_BYTE
from place.post import PostBase


class SimplePlaceTest(APITestBase):

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
        point1 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        place.lonLat = point1
        place.save()
        saved = Place.objects.first()
        self.assertEqual(place.lonLat, point1)
        self.assertEqual(saved.lonLat, point1)

        point2 = GEOSGeometry('POINT(127.107316 37.400998)')
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


class SimpleUserPlaceTest(APITestBase):

    def setUp(self):
        super(SimpleUserPlaceTest, self).setUp()
        self.place = Place()
        point = GEOSGeometry('POINT(127.1037430 37.3997320)')
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
        uplace, created = UserPlace.objects.get_or_create(vd=self.vd, place=self.place)
        self.assertEqual(created, True)
        uplace2, created = UserPlace.objects.get_or_create(vd=self.vd, place=self.place)
        self.assertEqual(created, False)
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
        point2 = GEOSGeometry('POINT(127.107316 37.400998)')
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


class PostTest(APITestBase):

    def test_post(self):
        place = Place(); place.save()
        vd1 = VD(); vd1.save()
        uplace1 = UserPlace(vd=vd1, place=place)
        uplace1.save()
        point1 = GEOSGeometry('POINT(127 37)')
        name1 = PlaceName(content='능라'); name1.save()
        addr1 = Address(content='경기도 성남시 분당구 운중동 883-3'); addr1.save()
        note11 = PlaceNote(content='분당 냉면 최고'); note11.save()
        note12 = PlaceNote(content='만두도 괜찮음'); note12.save()
        imgNote1 = ImageNote(content='냉면 사진'); imgNote1.save()
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        img1 = Image(content=img1_content); img1.save()
        phone1 = PhoneNumber(content='010-5686-1613'); phone1.save()

        vd2 = VD(); vd2.save()
        uplace2 = UserPlace(vd=vd2, place=place)
        uplace2.save()
        point2 = GEOSGeometry('POINT(127.1037430 37.3997320)')
        name2 = PlaceName(content='능라도'); name2.save()
        addr2 = Address(content='경기도 성남시 분당구 산운로32번길 12'); addr2.save()
        note21 = PlaceNote(content='여기 가게 바로 옆으로 이전'); note21.save()
        note22 = PlaceNote(content='평양냉면 맛집'); note22.save()
        img21_content = 'http://blogpfthumb.phinf.naver.net/20100110_16/mardukas_1263055491560_VI01Ic_JPG/DSCN1968.JPG'
        img22_content = 'http://mblogthumb1.phinf.naver.net/20160302_36/mardukas_14569226823176xNHG_JPEG/DSC07314.JPG'
        img21 = Image(content=img21_content); img21.save()
        img22 = Image(content=img22_content); img22.save()
        imgNote2 = ImageNote(content='만두 사진'); imgNote2.save()
        url2 = Url(content='http://maukistudio.com/'); url2.save()
        lp = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square'); lp.save();
        phone2 = PhoneNumber(content='010-5597-9245'); phone2.save()

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
        pp1 = PostPiece.objects.create(type_mask=0, place=None, uplace=uplace1, vd=vd1, data=pb1.json)
        self.assertEqual(PostPiece.objects.count(), 1)
        pp2 = PostPiece.objects.create(type_mask=0, place=None, uplace=uplace2, vd=vd2, data=pb2.json)
        pp3 = PostPiece.objects.create(type_mask=2, place=place, uplace=None, vd=vd1, data=pb2.json)
        self.assertEqual(PostPiece.objects.count(), 3)

        want_userPost = json_loads(json_userPost)
        want_placePost = json_loads(json_placePost)

        self.assertNotIn('timestamp', uplace1.userPost.json['lonLat'])
        self.assertNotIn('timestamp', uplace1.userPost.json['name'])
        self.assertIn('timestamp', uplace1.userPost.json['notes'][0])
        self.assertIn('timestamp', uplace1.userPost.json['images'][0])
        self.assertIn('timestamp', uplace1.userPost.json['images'][0]['note'])

        self.assertNotIn('timestamp', uplace2.userPost.json['urls'][0])
        self.assertNotIn('timestamp', uplace2.userPost.json['lps'][0])
        timestamp = uplace1.userPost.json['notes'][0]['timestamp']
        self.assertAlmostEqual(get_timestamp(), timestamp, delta=1000)
        self.assertIn('summary', uplace1.userPost.json['images'][0])
        self.assertIn('phone', uplace1.userPost.json)
        self.assertNotEqual(uplace1.userPost.json['images'][0]['content'], None)

        self.assertEqual(isSubsetOf(want_userPost, uplace1.userPost.json), True)
        self.assertEqual(isSubsetOf(uplace1.userPost.json, want_userPost), False)

        self.assertEqual(isSubsetOf(want_placePost, uplace1.place.placePost.json), True)
        self.assertEqual(isSubsetOf(uplace1.place.placePost.json, want_placePost), False)
        uplace1.clearCache()
        p1 = uplace1.place.placePost
        uplace2.clearCache()
        p2 = uplace2.place.placePost
        place.clearCache()
        p3 = place.placePost
        self.assertDictEqual(p1.json, p3.json)
        self.assertDictEqual(p2.json, p3.json)

    def test_change_place(self):
        vd = VD(); vd.save()
        pb_add = PostBase('{"urls": [{"content": "http://www.maukistudio.com/"}]}')
        pb_place1 = PostBase('{"urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=21149144"}]}')
        pb_place2 = PostBase('{"urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=31130096"}]}')

        uplace = UserPlace.get_from_post(pb_add, vd)
        self.assertEqual(uplace.place, None)

        pb_place1.uplace_uuid = uplace.uuid
        uplace = UserPlace.get_from_post(pb_place1.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        place1 = uplace.place

        pb_place2.uplace_uuid = uplace.uuid
        uplace = UserPlace.get_from_post(pb_place2.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        place2 = uplace.place
        self.assertNotEqual(place1, place2)

    def test_placed_by_name1(self):
        vd = VD(); vd.save()
        pb_add = PostBase('''{
            "lonLat": {"lon": 127.0584149999999966, "lat": 37.3916389999999978},
            "urls": [{"content": "http://www.maukistudio.com/"}]
        }''')
        pb_name = PostBase('{"name": {"content": "능이향기"}}')
        pb_place2 = PostBase('{"urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=31130096"}]}')

        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)
        uplace = UserPlace.get_from_post(pb_add, vd)
        self.assertEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)

        pb_name.uplace_uuid = uplace.uuid
        uplace = UserPlace.get_from_post(pb_name, vd)
        self.assertNotEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(PostPiece.objects.count(), 1)
        place1 = uplace.place
        self.assertEqual(place1.placePost.phone, None)

        pb_place2.uplace_uuid = uplace.uuid
        uplace = UserPlace.get_from_post(pb_place2.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        place2 = uplace.place
        self.assertEqual(place1, place2)
        self.assertEqual(Place.objects.count(), 1)
        self.assertNotEqual(place2.placePost.phone, None)
        self.assertEqual(PostPiece.objects.count(), 2)

    def __skip__test_placed_by_name2(self):
        vd = VD(); vd.save()
        pb_add = PostBase('''{
            "lonLat": {"lon": 127.0584149999999966, "lat": 37.3916389999999978},
            "urls": [{"content": "http://www.maukistudio.com/"}]
        }''')
        pb_name = PostBase('{"name": {"content": "능이향기"}}')
        pb_place2 = PostBase('{"urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=31130096"}]}')

        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)
        uplace = UserPlace.get_from_post(pb_add, vd)
        self.assertEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 0)
        self.assertEqual(PostPiece.objects.count(), 0)

        pb_place2.uplace_uuid = uplace.uuid
        uplace = UserPlace.get_from_post(pb_place2.pb_MAMMA, vd)
        self.assertNotEqual(uplace.place, None)
        place2 = uplace.place
        self.assertEqual(Place.objects.count(), 1)
        self.assertNotEqual(place2.placePost.phone, None)
        self.assertEqual(PostPiece.objects.count(), 1)

        pb_name.uplace_uuid = uplace.uuid
        uplace = UserPlace.get_from_post(pb_name, vd)
        self.assertNotEqual(uplace.place, None)
        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(PostPiece.objects.count(), 1)
        place1 = uplace.place
        self.assertEqual(place1, place2)
        self.assertNotEqual(place1.placePost.phone, None)


class PostPieceTest(APITestBase):

    def setUp(self):
        super(PostPieceTest, self).setUp()
        self.place = Place()
        self.place.save()
        self.uplace = UserPlace()
        self.uplace.save()
        self.vd = VD()
        self.vd.save()

        self.image = Image()
        img1_content = 'http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg'
        self.image.content = img1_content
        self.image.save()
        self.url = Url(content='http://maukistudio.com/')
        self.url.save()

        self.lp = LegacyPlace(content='4ccffc63f6378cfaace1b1d6.4square')
        self.lp.save()
        self.addr = Address(content='경기도 하남시 풍산로 270, 206동 402호 (선동, 미사강변도시2단지)')
        self.addr.save()
        self.phone = PhoneNumber(content='010-5597-9245')
        self.phone.save()

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

    def test_place_property(self):
        pp = PostPiece()
        pp.place = self.place
        pp.save()
        saved = self.place.pps.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.place, pp.place)

    def test_vd_property(self):
        pp = PostPiece()
        pp.vd = self.vd
        pp.save()
        saved = self.vd.pps.first()
        self.assertEqual(saved, pp)
        self.assertEqual(saved.vd, pp.vd)

    def test_data_property(self):
        pp = PostPiece()
        json_add = '''
            {
                "lonLat": {"lon": 127.1037430, "lat": 37.3997320},
                "images": [{"content": "http://blogthumb2.naver.net/20160302_285/mardukas_1456922688406bYGAH_JPEG/DSC07301.jpg"}],
                "addr1": {"content": "경기도 성남시 분당구 판교로 256번길 25"},
                "addr2": {"content": "경기도 성남시 분당구 삼평동 631"},
                "addr3": {"content": "경기도 성남시 분당구 삼평동"},
                "urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=21149144"}]
            }
        '''
        pp.data = json_add
        pp.save()
        saved = PostPiece.objects.first()
        self.assertEqual(json_add, pp.data)
        self.assertEqual(json_add, saved.data)

        # TODO : json 에 대한 query 테스트 추가


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
                "urls": [{"content": "http://map.naver.com/local/siteview.nhn?code=21149144"}]
            }
        '''
        pb = PostBase(json_add)
        json = pb.json
        pb2 = PostBase(json)
        self.assertDictEqual(json, pb2.json)
        self.assertEqual(isSubsetOf(json_loads(json_add), json), True)
        self.printJson(pb.pb_MAMMA)

