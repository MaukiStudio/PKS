 #-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from uuid import UUID
from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from json import loads as json_loads
from rest_framework import status
from hashlib import md5
from django.contrib.postgres.fields import JSONField
from re import compile as re_compile

from PIL import Image as PIL_Image, ImageOps as PIL_ImageOps
from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE, get_uuid_from_ts_vd
from base.models import Content
from base.legacy import exif_lib
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST, DISABLE_NO_FREE_API
from requests import get as requests_get
from pathlib2 import Path
from requests import post as requests_post

RAW_FILE_PATH = 'rfs/%Y/%m/%d/'
IMG_PD_HDIST_THREASHOLD = 36
IMG_P_HDIST_STRICT_THREASHOLD = 11
IMG_WH_MAX_SIZE = 1280
CONVERTED_DNS_LIST = [('http://maukitest.cloudapp.net', 'http://neapk-test01.japaneast.cloudapp.azure.com')]


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
        url = url_norms(raw_content)
        if url.startswith(SERVER_HOST):
            url = url[len(SERVER_HOST):]
        return url

    @property
    def url_for_access(self):
        _url = self.content.strip()
        if _url.startswith('http'):
            for converted in CONVERTED_DNS_LIST:
                if _url.startswith(converted[0]):
                    return _url.replace(converted[0], converted[1])
            return _url
        else:
            if _url.startswith('/'):
                return '%s%s' % (SERVER_HOST, _url)

        raise NotImplementedError

    def pre_save(self, is_created):
        if not self.rf:
            rf = RawFile.get_from_url(self.url_for_access)
            if rf:
                self.rf = rf
                self.access_local(self.rf.file.path)

        # TODO : 구조 단순하게 리팩토링. update_hash_exif 와의 연계도 고려
        try:
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
        except:
            pass

    def on_create(self):
        # celery task
        self.start()

    def update_hash_exif(self, save=True):
        pil = self.content_accessed
        self.phash = self.compute_phash(pil)
        self.dhash = self.compute_dhash(pil)
        if not self.lonLat or not self.timestamp:
            lonLat, timestamp = self.process_exif()
            self.lonLat = self.lonLat or lonLat
            self.timestamp = self.timestamp or timestamp
        if save:
            self.save()

    # TODO : priority 처리 구현
    def start(self, high_priority=False):
        from task_wrappers import AfterImageCreationTaskWrapper
        task = AfterImageCreationTaskWrapper()
        r = task.delay(self.id)

        # TODO : 정확한 구현인지 확인
        if r.failed():
            raise NotImplementedError
        return r

    def task(self, vd=None, force_hash=False, force_similar=False):
        if force_hash or not self.phash or not self.dhash:
            try:
                self.update_hash_exif(save=False)
            except:
                return False

        if force_similar or not self.lonLat or not self.timestamp:
            hamming_0 = [self.dhash]
            hamming_1 = [dhash ^ (1 << i) for dhash in hamming_0 for i in xrange(24)]
            hamming_2 = [dhash ^ (1 << i) for dhash in hamming_1 for i in xrange(24) if dhash ^ (1 << i) not in hamming_0]
            most_similar = None

            # 같은 디바이스의 사진들끼리의 처리
            if vd:
                rfs = RawFile.objects.filter(vd=vd.id).filter(same=None).exclude(mhash=None)
                similars = Image.objects.\
                    filter(rf__in=rfs).\
                    exclude(id=self.id).\
                    exclude(lonLat=None).\
                    exclude(timestamp=None)

                most_similar_dist = 121+24+1
                for similar in similars:
                    dist = self.pd_hamming_distance(similar)
                    if dist < most_similar_dist:
                        most_similar = similar
                        most_similar_dist = dist

                if most_similar_dist >= IMG_PD_HDIST_THREASHOLD:
                    most_similar = None

            # 다른 디바이스도 포함하여 전체 이미지에서의 처리
            if not most_similar:
                hamming = hamming_0 + hamming_1 + hamming_2
                similars = Image.objects.\
                    filter(dhash__in=hamming).\
                    exclude(id=self.id).\
                    exclude(lonLat=None).\
                    exclude(timestamp=None)

                most_similar_dist = 121+1
                for similar in similars:
                    dist = self.hamming_distance(self.phash, similar.phash)
                    if dist < most_similar_dist:
                        most_similar = similar
                        most_similar_dist = dist

                if most_similar_dist >= IMG_P_HDIST_STRICT_THREASHOLD:
                    most_similar = None

            # 결과 처리
            if most_similar:
                self.similar = most_similar
                self.lonLat = most_similar.lonLat
                self.timestamp = most_similar.timestamp

        # timestamp 만 있는 경우에 대한 lonLat guessing
        if not self.lonLat and (self.timestamp and vd):
            from importer.tasks import CLUSTERING_TIMEDELTA_THRESHOLD
            delta = (CLUSTERING_TIMEDELTA_THRESHOLD/2)*60*1000
            rfs = RawFile.objects.filter(vd=vd.id).filter(same=None).exclude(mhash=None)
            imgs = Image.objects.\
                filter(rf__in=rfs).\
                filter(timestamp__gte=(self.timestamp-delta)).\
                filter(timestamp__lte=(self.timestamp+delta)).\
                exclude(id=self.id).\
                exclude(lonLat=None).\
                exclude(timestamp=None)
            if imgs:
                from importer.tasks import CLUSTERING_MIN_DISTANCE_THRESHOLD, distance_geography
                img1 = imgs.filter(timestamp__lt=self.timestamp).order_by('-timestamp').first()
                img2 = imgs.filter(timestamp__gt=self.timestamp).order_by('timestamp').first()
                if img1 and img2:
                    if distance_geography(img1.lonLat, img2.lonLat) < CLUSTERING_MIN_DISTANCE_THRESHOLD:
                        ts1 = self.timestamp - img1.timestamp
                        ts2 = img2.timestamp - self.timestamp
                        lon = (img1.lonLat.x*ts2 + img2.lonLat.x*ts1) / (ts1 + ts2)
                        lat = (img1.lonLat.y*ts2 + img2.lonLat.y*ts1) / (ts1 + ts2)
                        self.lonLat = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
                        '''
                        print('')
                        print('ts1:%d, ts2:%d, lon:%0.4f, lat:%0.4f' % (ts1, ts2, self.lonLat.x, self.lonLat.y))
                        print(img1.url_summarized)
                        print(self.url_summarized)
                        print(img2.url_summarized)
                        print('')
                        #'''
                elif not img1 and img2:
                    if img2.timestamp - self.timestamp < delta/4:
                        self.lonLat = img2.lonLat
                        '''
                        print('')
                        print(self.url_summarized)
                        print(img2.url_summarized)
                        print('')
                        #'''

        # AzurePrediction
        azure, is_created = AzurePrediction.objects.get_or_create(img=self)
        if not self.rf or not self.rf.same:
            if is_created or not azure.result_analyze or\
                    ('statusCode' in azure.result_analyze and azure.result_analyze['statusCode'] == 429):
                azure.predict()

        self.save()
        return True

    @property
    def json(self):
        if self.note:
            return dict(uuid=self.uuid, content=self.url_for_access, summary=self.url_summarized, note=self.note.json)
        else:
            return dict(uuid=self.uuid, content=self.url_for_access, summary=self.url_summarized)
    @property
    def cjson(self):
        if self.note:
            return dict(content=self.url_for_access, summary=self.url_summarized, note=self.note.cjson)
        else:
            return dict(content=self.url_for_access, summary=self.url_summarized)
    @property
    def ujson(self):
        if self.note:
            return dict(uuid=self.uuid, note=self.note.cjson)
        else:
            return dict(uuid=self.uuid)

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
        exif = self._cache_accessed[1]
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

    def pd_hamming_distance(self, other):
        d_p = self.hamming_distance(self.phash, other.phash)
        d_d = self.hamming_distance(self.dhash, other.dhash)
        return d_p + d_d*2

    def p_hamming_distance(self, other):
        return self.hamming_distance(self.phash, other.phash)

    @property
    def content_accessed(self):
        if not self._cache_accessed:
            self.access()
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
            self._cache_accessed = (img, exif)
        return self._cache_accessed[0]

    def access_force(self, timeout=3):
        if self.rf:
            self.access_local(self.rf.file.path)
            return

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

    @classmethod
    def get_from_url(cls, url):
        if not url.startswith(SERVER_HOST):
            return None
        regex = re_compile('^.+/(?P<rf_id>[A-Fa-f0-9]+)\.rf_.+$')
        searcher = regex.search(url)
        if not searcher:
            return None
        rf_id = searcher.group('rf_id')
        if not rf_id:
            return None
        try:
            rf = cls.objects.get(id=rf_id)
        except:
            return None
        return rf

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

    @property
    def is_image(self):
        return self.ext in ('jpg', 'png')

    def save(self, *args, **kwargs):
        is_created = False

        # id/file 처리
        if not self.file:
            raise AssertionError
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            _id = self._id(timestamp)
            self.id = _id
            self.file.name = '%s_%s' % (self.uuid, self.file.name)
            is_created = True

        # 저장
        super(RawFile, self).save(*args, **kwargs)

    @property
    def url(self):
        return '%s%s' % (SERVER_HOST, self.file.url)

    @property
    def ext(self):
        ext = self.file.name.split('_')[-1].split('.')[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'
        return ext

    @property
    def is_symlink(self):
        with Path(self.file.path) as f:
            result = f.is_symlink()
        return result

    # TODO : priority 처리 구현
    def start(self, high_priority=False):
        from task_wrappers import AfterRawFileCreationTaskWrapper
        task = AfterRawFileCreationTaskWrapper()
        r = task.delay(self.id)

        # TODO : 정확한 구현인지 확인
        if r.failed():
            raise NotImplementedError
        return r

    def task(self):
        result = True
        is_symlink = self.is_symlink

        # Image Resize
        if not is_symlink and self.is_image:
            try:
                img = PIL_Image.open(self.file.path)
                w, h = img.size
                if w > IMG_WH_MAX_SIZE or h > IMG_WH_MAX_SIZE:
                    if w >= h:
                        w_new = IMG_WH_MAX_SIZE
                        h_new = int(round(float(IMG_WH_MAX_SIZE) * h / w))
                    else:
                        w_new = int(round(float(IMG_WH_MAX_SIZE) * w / h))
                        h_new = IMG_WH_MAX_SIZE
                    img = img.resize((w_new, h_new), PIL_Image.ANTIALIAS)
                    exif = 'exif' in img.info and img.info['exif'] or None
                    if exif:
                        img.save(self.file.path, exif=exif)
                    else:
                        img.save(self.file.path)
            except:
                result = False

        # Calc mhash
        if not is_symlink:
            m = md5()
            self.file.open()
            m.update(self.file.read())
            self.file.close()
            self.mhash = UUID(m.hexdigest())
        elif self.same:
            self.mhash = self.same.mhash
        else:
            print('symlinked but same property is None')
            raise NotImplementedError

        # process same
        same = self.find_same()
        if same and self != same:
            self.same = same
            self.mhash = self.same.mhash
            with Path(self.file.path) as f:
                f.unlink()
                f.symlink_to(same.file.path)

        # file process
        self.save()
        return result

    def find_same(self):
        if not self.mhash:
            return None
        sames = RawFile.objects.filter(mhash=self.mhash).order_by('id')
        self_file_size = None
        try:
            self_file_size = self.file.size
        except:
            pass
        same = None

        if sames:
            for rf in sames:
                # find same safely
                # 실섭에서 이상하게도 cyclic symbolic link 가 발견되었는데, 이에 대한 대응
                if rf.is_symlink:
                    continue
                # TODO : 이걸로 동일성 체크가 충분하지 않다면 실제 file 내용 일부 비교 추가 혹은 sha128 추가 및 활용
                if self.ext == rf.ext and (not self_file_size or self_file_size == rf.file.size):
                    same = rf
                    break

        if same == self:
            same = None
        return same


class AzurePrediction(models.Model):
    img = models.OneToOneField(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='azure')
    mask = models.SmallIntegerField(blank=True, null=True, default=None)
    result_analyze = JSONField(blank=True, null=True, default=None, db_index=False)

    @property
    def is_success_analyze(self):
        return (self.mask or 0) & 1 != 0
    @is_success_analyze.setter
    def is_success_analyze(self, value):
        if value:
            self.mask = (self.mask or 0) | 1
        else:
            self.mask = (self.mask or 0) & (~1)

    def predict(self, idx=None, level=0):
        '''
            POST https://api.projectoxford.ai/vision/v1.0/analyze?visualFeatures=ImageType,Faces,Adult,Categories,Color,Tags,Description&details=Celebrities HTTP/1.1
            Content-Type: application/json
            Host: api.projectoxford.ai
            Content-Length: 120
            Ocp-Apim-Subscription-Key: d91fa94bcd484158a74d9463826b689c

            {"url":"http://maukitest.cloudapp.net/media/rfs/2016/07/15/00000155EDBB32190000000000D4ECE0.rf_image.jpg?1434956498000"}
        '''
        if DISABLE_NO_FREE_API:
            return None
        if not self.img or not self.img.url_for_access:
            return None
        if self.img.url_for_access.startswith('http://192.'):
            return None

        api_key = ['d91fa94bcd484158a74d9463826b689c',
                   'e8312a7a2a2e4fc5b09624bfbbe861b7',
                   '76f32cbb42c644abb8daf3aa105335aa',
                   '8c96d76d3a2341189c06d9c86c417940',
                   '9d15c869c53847bf8b2efb2283af342a',
                   'efe9e8f5e64d43a490f5310f162d8fa7',
                   '8db18bd1adaf474ea7a2fb969e885583',
                   '1bcda2d979ab4266ae032f0adeb579f4',
                   '98f3ee698d3a4a2595856806ad133f33',
                   '7da3a83c46a74c50af15a43a673e757b',
                   'd3487f984f624d799b3c8a255877d2a5',]
        cnt = len(api_key)
        if level >= cnt:
            return None
        if idx is None:
            from random import randrange
            idx = randrange(0, cnt)
        headers = {'Content-Type': 'application/json', 'Ocp-Apim-Subscription-Key': api_key[idx]}
        api_url = 'https://api.projectoxford.ai/vision/v1.0/analyze?visualFeatures=ImageType,Faces,Adult,Categories,Color,Tags,Description&details=Celebrities'
        data = '{"url": "%s"}' % self.img.url_for_access
        try:
            r = requests_post(api_url, headers=headers, data=data, timeout=60)
        except:
            return None
        self.is_success_analyze = (r.status_code == status.HTTP_200_OK)
        result = json_loads(r.content)
        if not self.is_success_analyze and 'statusCode' in result and result['statusCode'] == 429:
            from re import compile as re_compile
            regex = re_compile(r'Rate limit is exceeded\. Try again in (?P<seconds>[0-9]+) seconds\.')
            searcher = regex.search(result['message'])
            seconds = searcher.group('seconds')
            if seconds:
                from time import sleep
                print('sleep for %s seconds...')
                if seconds > 60:
                    seconds = 60
                sleep(seconds)
                return self.predict((idx+1) % cnt, level+1)
        self.result_analyze = result
        self.save()

        if self.is_success_analyze:
            self.tagging()
        return result

    def tagging(self):
        from tag.models import ImageTags
        imgTags, is_created = ImageTags.objects.get_or_create(img=self.img)
        imgTags.process_azure_tag(self)
        imgTags.save()
        return imgTags
