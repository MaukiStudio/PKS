#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from json import loads as json_loads
from rest_framework import status
from hashlib import md5

from PIL import Image as PIL_Image, ImageOps as PIL_ImageOps
from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE, get_uuid_from_ts_vd
from base.models import Content
from base.legacy import exif_lib
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST
from requests import get as requests_get
from pathlib2 import Path


RAW_FILE_PATH = 'rfs/%Y/%m/%d/'
# 41 부터 완전히 다른 이미지가 나오기 시작. 40도 한번 문제가 관측됨. So 39 까지는 괜찮아 보임
PHASH11_THREASHOLD = 40


class Image(Content):
    phash = models.UUIDField(blank=True, null=True, default=None)
    dhash = models.BigIntegerField(blank=True, null=True, default=None, db_index=True)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    timestamp = models.BigIntegerField(blank=True, null=True, default=None)
    rf = models.OneToOneField('RawFile', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='img', db_index=True)
    similar = models.ForeignKey('self', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='similars')

    # MUST override
    @property
    def contentType(self):
        return 'img'

    @property
    def accessedType(self):
        return 'jpg'

    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        return url_norms(raw_content)

    def pre_save(self):
        # TODO : 구조 단순하게 리팩토링
        if self.is_accessed and not (self.lonLat and self.timestamp and self.phash and self.dhash and self.is_summarized):
            pil = self.content_accessed
            if pil:
                if not self.lonLat or not self.timestamp:
                    lonLat, timestamp = self.process_exif()
                    self.lonLat = self.lonLat or lonLat
                    self.timestamp = self.timestamp or timestamp
                if not self.phash:
                    self.phash = self.compute_phash(pil)
                if not self.dhash:
                    self.dhash = self.compute_dhash(pil)
                self.summarize(pil)

    def task(self, vd=None, force_hash=False, force_similar=False):
        if force_hash or not self.phash or not self.dhash:
            self.access()
            try:
                pil = self.content_accessed
                self.phash = self.compute_phash(pil)
                self.dhash = self.compute_dhash(pil)
            except:
                return False

        if force_similar or not self.lonLat or not self.timestamp:
            hamming_0 = [self.dhash]
            hamming_1 = [dhash ^ (1 << i) for dhash in hamming_0 for i in xrange(24)]
            hamming_2 = [dhash ^ (1 << i) for dhash in hamming_1 for i in xrange(24) if dhash ^ (1 << i) not in hamming_0]
            most_similar = None

            # 같은 디바이스의 사진들끼리의 처리
            if vd:
                hamming = hamming_0 + hamming_1 + hamming_2
                rfs = RawFile.objects.filter(vd=vd.id).filter(same=None).exclude(mhash=None)
                similars = Image.objects.\
                    filter(rf__in=rfs).\
                    filter(dhash__in=hamming).\
                    filter(similar=None).\
                    exclude(id=self.id).\
                    exclude(lonLat=None).\
                    exclude(timestamp=None)

                most_similar_dist = 128+1
                for similar in similars:
                    dist = self.hamming_distance(self.phash, similar.phash)
                    if dist < most_similar_dist:
                        most_similar = similar
                        most_similar_dist = dist

                if most_similar_dist >= PHASH11_THREASHOLD:
                    most_similar = None

            # 다른 디바이스도 포함하여 전체 이미지에서의 처리
            if not most_similar:
                # dhash diff 1 까지만 index 조회한다
                hamming = hamming_0 + hamming_1
                similars = Image.objects.\
                    filter(dhash__in=hamming).\
                    filter(similar=None).\
                    exclude(id=self.id).\
                    exclude(lonLat=None).\
                    exclude(timestamp=None)

                most_similar_dist = 128+1
                for similar in similars:
                    dist = self.hamming_distance(self.phash, similar.phash)
                    if dist < most_similar_dist:
                        most_similar = similar
                        most_similar_dist = dist

                # 훨씬 더 가혹한 기준이 적용되어야 안전
                # 최소한 2까지는 포함해야 함 (Tested)
                # 명확한 실험결과는 아니나... 일단 5%, 즉 6 으로 적용
                if most_similar_dist > 6:
                    most_similar = None

            # 결과 처리
            if most_similar:
                self.similar = most_similar
                self.lonLat = most_similar.lonLat
                self.timestamp = most_similar.timestamp

        self.save()
        return True

    @property
    def json(self):
        if self.timestamp:
            if self.note:
                return dict(uuid=self.uuid, content=self.content, note=self.note.json, timestamp=self.timestamp, summary=self.url_summarized)
            else:
                return dict(uuid=self.uuid, content=self.content, timestamp=self.timestamp, summary=self.url_summarized)
        else:
            if self.note:
                return dict(uuid=self.uuid, content=self.content, note=self.note.json, summary=self.url_summarized)
            else:
                return dict(uuid=self.uuid, content=self.content, summary=self.url_summarized)

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self.note = None

    @classmethod
    def get_from_json(cls, json):
        if type(json) is unicode or type(json) is str:
            json = json_loads(json)
        result = super(Image, cls).get_from_json(json)
        if result and 'note' in json and json['note']:
            from content.models import ImageNote
            result.note = ImageNote.get_from_json(json['note'])
        return result

    # Image's method
    @classmethod
    def compute_phash(cls, pil):
        from imagehash import phash
        d = phash(pil, hash_size=11)
        return UUID(str(d).rjust(32, b'0'))

    @classmethod
    def compute_dhash(cls, pil):
        from imagehash import dhash
        d = dhash(pil, hash_size=6)
        r = 0
        bitarr = d.hash.flatten()
        use = [2, 3, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28, 32, 33]
        #not_use = [0, 1, 4, 5, 6, 11, 24, 29, 30, 31, 34, 35]
        for bit in bitarr[use]:
            r = r*2 + bit
        return r

    def process_exif(self):
        pil = self.content_accessed
        exif = self._accessed_cache[1]
        result = [None, None]
        if exif:
            lonLat = exif_lib.get_lon_lat(exif)
            if lonLat and lonLat[0] and lonLat[1]:
                result[0] = GEOSGeometry('POINT(%f %f)' % lonLat, srid=4326)
            timestamp = exif_lib.get_timestamp(exif)
            if timestamp:
                result[1] = timestamp
        return result

    def summarize_force(self, accessed=None):
        if not accessed:
            accessed = self.content_accessed
        if accessed:
            thumb = PIL_ImageOps.fit(accessed, (300, 300), PIL_Image.ANTIALIAS).convert('RGB')
            thumb.save(self.path_summarized)

    @classmethod
    def hamming_distance(cls, hash1, hash2):
        v1, v2 = int(hash1), int(hash2)
        count, z = 0, v1 ^ v2
        while z:
            count += 1
            z &= z - 1
        return count

    @property
    def content_accessed(self):
        if not self._accessed_cache:
            img = None
            exif = None
            try:
                img = PIL_Image.open(self.path_accessed)
                exif = exif_lib.get_exif_data(img)
                img = exif_lib.transpose_image_by_exif(img)
            except IOError:
                pass
            except AttributeError:
                pass
            self._accessed_cache = (img, exif)
        return self._accessed_cache[0]

    def access_force(self, timeout=3):
        headers = {'user-agent': 'Chrome'}
        r = requests_get(self.url_for_access, headers=headers, timeout=timeout)
        if r.status_code not in (status.HTTP_200_OK,):
            print('Access failed : %s' % self.url_for_access)

        file = Path(self.path_accessed)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)
        summary = Path(self.path_summarized)
        if not Path(self.path_summarized).parent.exists():
            summary.parent.mkdir(parents=True)
        file.write_bytes(r.content)


class RawFile(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    file = models.FileField(blank=True, null=True, default=None, upload_to=RAW_FILE_PATH)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='rfs')
    mhash = models.UUIDField(blank=True, null=True, default=None, db_index=True)
    same = models.ForeignKey('self', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='sames')

    @property
    def uuid(self):
        return '%s.rf' % b16encode(self.id.bytes)

    def __unicode__(self):
        return self.uuid

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        return get_uuid_from_ts_vd(timestamp, vd_id)

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    def save(self, *args, **kwargs):
        # id/file 처리
        if not self.file:
            raise AssertionError
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            _id = self._id(timestamp)
            self.id = _id
            self.file.name = '%s_%s' % (self.uuid, self.file.name)

        # 저장
        super(RawFile, self).save(*args, **kwargs)

        # 이미지인 경우 바로 캐시 처리 및 Image object 생성
        if self.ext in ('jpg', 'png'):
            img = Image(content=self.url)
            img.content = img.normalize_content(img.content)
            if not img.content.startswith('http'):
                raise ValueError('Invalid image URL')
            img.id = img._id
            img.access_local(self.file.path)
            img.rf = self
            img.save()

    @property
    def url(self):
        return '%s%s' % (SERVER_HOST, self.file.url)

    @property
    def ext(self):
        ext = self.file.name.split('_')[-1].split('.')[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
        return ext

    def task(self):
        try:
            m = md5()
            self.file.open()
            m.update(self.file.read())
            self.file.close()
            self.mhash = UUID(m.hexdigest())
        except:
            # TODO : 파일이 삭제되거나 손상된 RawFile 을 어떻게 처리할지 결정 및 구현 필요
            return False

        sames = RawFile.objects.filter(mhash=self.mhash).order_by('id')
        if sames:
            same = sames[0]
            if self != same:
                # TODO : 이걸로 동일성 체크가 충분하지 않다면 실제 file 내용 일부 비교 추가 혹은 sha128 추가 및 활용
                if self.ext == same.ext and self.file.size == same.file.size:
                    self.same = same
                    with Path(self.file.path) as f:
                        f.unlink()
                        f.symlink_to(same.file.path)

        self.save()
        return True
