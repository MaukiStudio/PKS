#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from rest_framework import status
from json import loads as json_loads

from base.tests import FunctionalTestAfterLoginBase
from importer.models import Proxy, Importer
from account.models import VD, RealUser
from place.models import UserPlace, Place, PostPiece
from place.post import PostBase
from image.models import Image


class ImportedPlaceViewSetTest(FunctionalTestAfterLoginBase):

    def setUp(self):
        super(ImportedPlaceViewSetTest, self).setUp()

        # ru1 : myself
        self.ru1 = self.vd.realOwner
        self.vd11 = self.vd
        self.vd12 = VD.objects.create(realOwner=self.ru1)
        self.vd12_album = VD.objects.create(parent=self.vd12, is_private=True, is_public=False)
        self.proxy_vd12_album = Proxy.objects.create(vd=self.vd12_album, guide={'type': 'images', 'vd': self.vd12.id})
        self.importer_vd12_album = Importer.objects.create(publisher=self.proxy_vd12_album, subscriber=self.vd12)

        # ru2 : ru1 --> ru2
        self.ru2_email = 'gulby@naver.com'
        self.ru2 = RealUser.objects.create(email=self.ru2_email)
        self.vd21 = VD.objects.create(realOwner=self.ru2)
        self.vd22 = VD.objects.create(realOwner=self.ru2)
        self.vd22_album = VD.objects.create(parent=self.vd22, is_private=True, is_public=False)
        self.proxy_vd22_album = Proxy.objects.create(vd=self.vd22_album, guide={'type': 'images', 'vd': self.vd22.id})
        self.importer_vd22_album = Importer.objects.create(publisher=self.proxy_vd22_album, subscriber=self.vd22)

        # ru3 : ru2 --> ru3
        self.ru3_email = 'gullbynet@hanmail.net'
        self.ru3 = RealUser.objects.create(email=self.ru3_email)
        self.vd31 = VD.objects.create(realOwner=self.ru3)
        self.vd32 = VD.objects.create(realOwner=self.ru3)
        self.vd32_album = VD.objects.create(parent=self.vd32, is_private=True, is_public=False)
        self.proxy_vd32_album = Proxy.objects.create(vd=self.vd32_album, guide={'type': 'images', 'vd': self.vd32.id})
        self.importer_vd32_album = Importer.objects.create(publisher=self.proxy_vd32_album, subscriber=self.vd32)

        # make user importers
        self.vd2_virtual = VD.objects.create()
        self.proxy_ru2 = Proxy.objects.create(vd=self.vd2_virtual, guide={'type': 'user', 'email': self.ru2_email})
        self.importer_ru1_ru2 = Importer.objects.create(publisher=self.proxy_ru2, subscriber=self.vd11)
        self.vd3_virtual = VD.objects.create()
        self.proxy_ru3 = Proxy.objects.create(vd=self.vd3_virtual, guide={'type': 'user', 'email': self.ru3_email})
        self.importer_ru2_ru3 = Importer.objects.create(publisher=self.proxy_ru3, subscriber=self.vd21)

        # make images
        self.url11 = 'http://www.maukistudio.com/img11.jpg'
        self.img11 = Image.objects.create(content=self.url11)
        self.url12 = 'http://www.maukistudio.com/img12.jpg'
        self.img12 = Image.objects.create(content=self.url12)
        self.url12_album = 'http://www.maukistudio.com/img12_album.jpg'
        self.img12_album = Image.objects.create(content=self.url12_album)
        self.url21 = 'http://www.maukistudio.com/img21.jpg'
        self.img21 = Image.objects.create(content=self.url21)
        self.url22 = 'http://www.maukistudio.com/img22.jpg'
        self.img22 = Image.objects.create(content=self.url22)
        self.url22_album = 'http://www.maukistudio.com/img22_album.jpg'
        self.img22_album = Image.objects.create(content=self.url22_album)
        self.url31 = 'http://www.maukistudio.com/img31.jpg'
        self.img31 = Image.objects.create(content=self.url31)
        self.url32 = 'http://www.maukistudio.com/img32.jpg'
        self.img32 = Image.objects.create(content=self.url32)
        self.url32_album = 'http://www.maukistudio.com/img32_album.jpg'
        self.img32_album = Image.objects.create(content=self.url32_album)

        # make places
        self.place11 = Place.objects.create()
        self.place12 = Place.objects.create()
        self.place12_album = Place.objects.create()
        self.place21 = Place.objects.create()
        self.place22 = Place.objects.create()
        self.place22_album = Place.objects.create()
        self.place31 = Place.objects.create()
        self.place32 = Place.objects.create()
        self.place32_album = Place.objects.create()

        # make uplaces
        self.uplace11 = UserPlace.objects.create(vd=self.vd11, place=self.place11)
        self.uplace12 = UserPlace.objects.create(vd=self.vd12, place=self.place12)
        self.uplace12_album = UserPlace.objects.create(vd=self.vd12_album, place=self.place12_album)
        self.uplace21 = UserPlace.objects.create(vd=self.vd21, place=self.place21)
        self.uplace22 = UserPlace.objects.create(vd=self.vd22, place=self.place22)
        self.uplace22_album = UserPlace.objects.create(vd=self.vd22_album, place=self.place22_album)
        self.uplace31 = UserPlace.objects.create(vd=self.vd31, place=self.place31)
        self.uplace32 = UserPlace.objects.create(vd=self.vd32, place=self.place32)
        self.uplace32_album = UserPlace.objects.create(vd=self.vd32_album, place=self.place32_album)

        # make postbase
        self.pb11 = PostBase(); self.pb11.images.append(self.img11)
        self.pb12 = PostBase(); self.pb12.images.append(self.img12)
        self.pb12_album = PostBase(); self.pb12_album.images.append(self.img12_album)
        self.pb21 = PostBase(); self.pb21.images.append(self.img21)
        self.pb22 = PostBase(); self.pb22.images.append(self.img22)
        self.pb22_album = PostBase(); self.pb22_album.images.append(self.img22_album)
        self.pb31 = PostBase(); self.pb31.images.append(self.img31)
        self.pb32 = PostBase(); self.pb32.images.append(self.img32)
        self.pb32_album = PostBase(); self.pb32_album.images.append(self.img32_album)

        # make postpiece
        uplace = self.uplace11; pb = self.pb11
        self.pp11 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace12; pb = self.pb12
        self.pp12 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace12_album; pb = self.pb12_album
        self.pp12_album = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace21; pb = self.pb21
        self.pp21 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace22; pb = self.pb22
        self.pp22 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace22_album; pb = self.pb22_album
        self.pp22_album = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace31; pb = self.pb31
        self.pp31 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace32; pb = self.pb32
        self.pp32 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)
        uplace = self.uplace32_album; pb = self.pb32_album
        self.pp32_album = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)

        #self.reset_cache()

    def reset_cache(self):
        self.clear_cache_ru(self.ru1)
        self.clear_cache_ru(self.ru2)
        self.clear_cache_ru(self.ru3)

    def take(self, iplace, vd):
        pb = PostBase()
        pb.iplace_uuid = iplace.uuid
        pb.place_id = iplace.place_id
        pb.uplace_uuid = None
        uplace, is_created = UserPlace.get_or_create_smart(pb, vd)
        pp = PostPiece.create_smart(uplace, pb)
        #self.reset_cache()
        return uplace

    def assertMembersIn(self, members, container):
        for member in members:
            self.assertIn(member, container)

    def assertMembersNotIn(self, members, container):
        for member in members:
            self.assertNotIn(member, container)


    def test_uplaces_basic(self):
        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 2)
        self.assertMembersIn([self.url11, self.url12], response.content)
        self.assertMembersNotIn([self.url12_album,
                                 self.url21, self.url22, self.url22_album,
                                 self.url31, self.url32, self.url32_album], response.content)

    def test_iplaces_basic(self):
        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)
        self.assertMembersIn([self.url12_album, self.url21, self.url22], response.content)
        self.assertMembersNotIn([self.url11, self.url12,
                                 self.url22_album,
                                 self.url31, self.url32, self.url32_album], response.content)

    def test_uplaces_after_ru1_take_album(self):
        iplace12_album = self.take(self.uplace12_album, self.vd12)
        self.assertNotEqual(iplace12_album, self.uplace12_album)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)
        self.assertMembersIn([self.url11, self.url12, self.url12_album], response.content)
        self.assertMembersNotIn([
                                 self.url21, self.url22, self.url22_album,
                                 self.url31, self.url32, self.url32_album], response.content)

    def test_iplaces_after_ru2_take_album(self):
        iplace22_album = self.take(self.uplace22_album, self.vd22)

        response = self.client.get('/iplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 4)
        self.assertMembersIn([self.url12_album, self.url21, self.url22], response.content)
        self.assertMembersNotIn([self.url11, self.url12,
                                 self.url22_album,
                                 self.url31, self.url32, self.url32_album], response.content)

    def test_uplaces_after_ru2_take_album_and_ru1_take_all(self):
        iplace22_album = self.take(self.uplace22_album, self.vd22)

        iplace12_album = self.take(self.uplace12_album, self.vd12)
        iplace21 = self.take(self.uplace21, self.vd11)
        iplace22 = self.take(self.uplace22, self.vd11)
        iiplace22_album = self.take(iplace22_album, self.vd11)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 6)
        self.assertMembersIn([self.url11, self.url12, self.url12_album,
                              self.url21, self.url22], response.content)
        self.assertMembersNotIn([
            self.url22_album,
            self.url31, self.url32, self.url32_album], response.content)

    def test_uplaces_illegal_take1(self):
        iplace22_album = self.take(self.uplace22_album, self.vd11)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 3)
        self.assertMembersIn([self.url11, self.url12], response.content)
        self.assertMembersNotIn([self.url12_album,
                                 self.url21, self.url22, self.url22_album,
                                 self.url31, self.url32, self.url32_album], response.content)

    def test_uplaces_illegal_take2(self):
        iplace31 = self.take(self.uplace31, self.vd11)
        iplace32 = self.take(self.uplace32, self.vd11)
        iplace32_album = self.take(self.uplace32_album, self.vd11)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 5)
        self.assertMembersIn([self.url11, self.url12], response.content)
        self.assertMembersNotIn([self.url12_album,
                                 self.url21, self.url22, self.url22_album,
                                 self.url31, self.url32, self.url32_album], response.content)

    def test_uplaces_total(self):
        iplace32_album = self.take(self.uplace32_album, self.vd32)

        iplace22_album = self.take(self.uplace22_album, self.vd22)
        iplace31 = self.take(self.uplace31, self.vd22)
        iplace32 = self.take(self.uplace32, self.vd22)
        iiplace32_album = self.take(iplace32_album, self.vd22)

        iplace12_album = self.take(self.uplace12_album, self.vd12)
        iplace21 = self.take(self.uplace21, self.vd11)
        iplace22 = self.take(self.uplace22, self.vd11)
        iiplace22_album = self.take(iplace22_album, self.vd11)
        iiplace31 = self.take(iplace31, self.vd11)
        iiplace32 = self.take(iplace32, self.vd11)
        iiiplace32_album = self.take(iiplace32_album, self.vd11)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 9)
        self.assertMembersIn([self.url11, self.url12, self.url12_album,
                              self.url21, self.url22], response.content)
        self.assertMembersNotIn([
            self.url22_album,
            self.url31, self.url32, self.url32_album], response.content)

        # add image
        url22_album_2 = 'http://www.maukistudio.com/img22_album_2.jpg'
        img22_album_2 = Image.objects.create(content=url22_album_2)
        pb22_album_2 = PostBase(); pb22_album_2.images.append(img22_album_2)
        uplace = iplace22_album; pb = pb22_album_2
        pp22_album_2 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)

        url32_album_2 = 'http://www.maukistudio.com/img32_album_2.jpg'
        img32_album_2 = Image.objects.create(content=url32_album_2)
        pb32_album_2 = PostBase(); pb32_album_2.images.append(img32_album_2)
        uplace = iiplace32_album; pb = pb32_album_2
        pp32_album_2 = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 9)
        self.assertMembersIn([self.url11, self.url12, self.url12_album,
                              self.url21, self.url22, url22_album_2, url32_album_2], response.content)
        self.assertMembersNotIn([
            self.url22_album,
            self.url31, self.url32, self.url32_album], response.content)

        # ru1 imports ru3
        self.importer_ru1_ru3 = Importer.objects.create(publisher=self.proxy_ru3, subscriber=self.vd11)

        response = self.client.get('/uplaces/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.content)
        results = json_loads(response.content)['results']
        self.assertEqual(len(results), 9)
        self.assertMembersIn([self.url11, self.url12, self.url12_album,
                              self.url21, self.url22, url22_album_2, url32_album_2,
                              self.url31, self.url32], response.content)
        self.assertMembersNotIn([
            self.url22_album,
            self.url32_album], response.content)
