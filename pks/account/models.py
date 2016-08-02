#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import sha256
from base64 import urlsafe_b64encode
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models import Count

from cryptography.fernet import Fernet
from pks.settings import VD_ENC_KEY
from base.utils import get_timestamp, BIT_ON_6_BYTE, BIT_ON_8_BYTE
from base.cache import cache_get_or_create, cache_expire_ru


class User(AbstractUser):

    def __init__(self, *args, **kwargs):
        self._cache_crypto_key = None
        super(User, self).__init__(*args, **kwargs)

    @property
    def crypto_key(self):
        if not self._cache_crypto_key:
            raw_key = '%d|%s' % (self.id, VD_ENC_KEY)
            h = sha256()
            h.update(raw_key)
            self._cache_crypto_key = urlsafe_b64encode(h.digest())
        return self._cache_crypto_key

    def aid2id(self, aid):
        decrypter = Fernet(self.crypto_key)
        result = decrypter.decrypt(aid.encode(encoding='utf-8'))
        return int(result)


class RealUser(models.Model):
    email = models.EmailField(unique=True, blank=False, null=False, default=None)

    def __init__(self, *args, **kwargs):
        self._vd_ids_cache = None
        super(RealUser, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.email

    @property
    def vd_ids(self):
        if not self._vd_ids_cache:
            self._vd_ids_cache = [vd.id for vd in self.vds.all()]
        return self._vd_ids_cache

    def save(self, *args, **kwargs):
        if not self.email:
            raise ValueError('RealUser.email cannot be None')
        self.email = BaseUserManager.normalize_email(self.email)
        super(RealUser, self).save(*args, **kwargs)


class VD(models.Model):
    authOwner = models.ForeignKey(User, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='vds')
    realOwner = models.ForeignKey(RealUser, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='vds')

    lastLonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    data = JSONField(blank=True, null=True, default=None, db_index=False)

    deviceName = models.CharField(max_length=254, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)

    country = models.CharField(max_length=2, blank=True, null=True, default=None)
    language = models.CharField(max_length=2, blank=True, null=True, default=None)
    timezone = models.CharField(max_length=5, blank=True, null=True, default=None)

    parent = models.ForeignKey('self', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='childs')
    mask = models.SmallIntegerField(blank=True, null=True, default=None)

    accessHistory = JSONField(blank=True, null=True, default=None, db_index=False)


    def __init__(self, *args, **kwargs):
        super(VD, self).__init__(*args, **kwargs)

    def __unicode__(self):
        email = (self.realOwner and self.realOwner.email) or (self.authOwner and self.authOwner.email) or 'unknown@email'
        deviceTypeName = self.deviceTypeName or 'unknown device'
        deviceNameCaption = (self.deviceName and ' (%s)' % self.deviceName) or ''
        return '%s\'s %s%s' % (email, deviceTypeName, deviceNameCaption)

    @property
    def aid(self):
        encrypter = Fernet(self.authOwner.crypto_key)
        result = encrypter.encrypt(unicode(self.id).encode(encoding='utf-8'))
        return result

    def aid2id(self, aid):
        return self.authOwner.aid2id(aid)

    @property
    def realOwner_vd_ids(self):
        if self.realOwner:
            result, is_created = cache_get_or_create(self, 'realOwner_vd_ids', None, lambda: self.realOwner.vd_ids)
            return result
        return [self.id]

    @property
    def realOwner_publisher_ids(self):
        def helper(vd_ids):
            from importer.models import Importer
            importers = Importer.objects.filter(subscriber_id__in=vd_ids)
            if importers:
                return sum([importer.publisher.vd_ids for importer in importers], [])
            else:
                return []
        result, is_created = cache_get_or_create(self, 'realOwner_publisher_ids', None, helper, self.realOwner_vd_ids)
        return result

    @property
    def realOwner_place_ids(self):
        def helper(vd_ids):
            from place.models import Place
            return [place.id for place in Place.objects.filter(uplaces__vd_id__in=vd_ids)]
        result, is_created = cache_get_or_create(self, 'realOwner_place_ids', None, helper, self.realOwner_vd_ids)
        return result

    @property
    def realOwner_duplicated_uplace_ids(self):
        def helper(vd_ids):
            from place.models import UserPlace
            base = UserPlace.objects.all().exclude(place_id=None).filter(vd_id__in=vd_ids)
            group_by = base.values('place_id').annotate(cnt=Count(1)).filter(cnt__gte=2)
            result = list()
            before = None
            for uplace in base.filter(place_id__in=[row['place_id'] for row in group_by]).order_by('place_id', '-id'):
                if uplace.place_id == (before and before.place_id):
                    result.append(uplace.id)
                before = uplace
            return result
        result, is_created = cache_get_or_create(self, 'realOwner_duplicated_uplace_ids', None, helper, self.realOwner_vd_ids)
        return result

    @property
    def realOwner_duplicated_iplace_ids(self):
        def helper(vd_ids):
            from importer.models import ImportedPlace
            base = ImportedPlace.objects.all().exclude(place_id=None).filter(vd_id__in=vd_ids)
            group_by = base.values('place_id').annotate(cnt=Count(1)).filter(cnt__gte=2)
            result = list()
            before = None
            for iplace in base.filter(place_id__in=[row['place_id'] for row in group_by]).order_by('place_id', '-id'):
                if iplace.place_id == (before and before.place_id):
                    result.append(iplace.id)
                before = iplace
            return result
        result, is_created = cache_get_or_create(self, 'realOwner_duplicated_iplace_ids', None, helper, self.realOwner_publisher_ids)
        return result

    @property
    def is_private(self):
        return (self.mask or 0) & 1 != 0
    @is_private.setter
    def is_private(self, value):
        if value:
            self.mask = (self.mask or 0) | 1
        else:
            self.mask = (self.mask or 0) & (~1)

    @property
    def is_public(self):
        return (self.mask or 0) & 2 != 0
    @is_public.setter
    def is_public(self, value):
        if value:
            self.mask = (self.mask or 0) | 2
        else:
            self.mask = (self.mask or 0) & (~2)

    def save(self, *args, **kwargs):
        if not self.mask:
            self.mask = 0
        if self.realOwner:
            cache_expire_ru(self.realOwner, 'realOwner_vd_ids')
        super(VD, self).save(*args, **kwargs)

    # TODO : 제대로 구현하기
    @property
    def error_tagging_ratio(self):
        # P(D|~H) / P(D|H)
        return 0.2

    def getToken(self):
        raw_token = '%s|%s' % (self.id, self.authOwner_id)
        encrypter = Fernet(self.authOwner.crypto_key)
        return encrypter.encrypt(raw_token.encode(encoding='utf-8'))

    def getEmailConfirmToken(self, email):
        from pks.settings import VD_ENC_KEY
        raw_token = '%s|%s' % (self.id, email)
        encrypter = Fernet(VD_ENC_KEY)
        return encrypter.encrypt(raw_token.encode(encoding='utf-8'))

    def add_access_history(self, uplaces):
        if not self.accessHistory:
            self.accessHistory = dict(uplaces=[])
        if not type(uplaces) is list:
            uplaces = [uplaces]
        for uplace in uplaces:
            uuid = uplace.uuid
            timestamp = get_timestamp()
            self.accessHistory['uplaces'].insert(0, dict(uuid=uuid, timestamp=timestamp))
        super(VD, self).save()

    @property
    def accessUplaces(self):
        from place.models import UserPlace
        result = []
        if self.accessHistory and 'uplaces' in self.accessHistory:
            for d in self.accessHistory['uplaces']:
                uplace = UserPlace.get_from_uuid(d['uuid'])
                uplace.accessed = d['timestamp']
                result.append(uplace)
        return result

    def send_confirm_email(self, email):
        # send email for confirm
        # TODO : 관련 테스트 보강
        from account.task_wrappers import EmailTaskWrapper
        from pks.settings import SERVER_HOST
        task = EmailTaskWrapper()
        to = email
        title = '[PlaceKoob] 이메일 인증'
        confirm_link = '%s/vds/confirm/?email_confirm_token=%s' % (SERVER_HOST, self.getEmailConfirmToken(to))
        msg = '안녕하세요. PlaceKoob 입니다.\n이메일 인증을 위해 하기 링크를 터치해 주세요.\n\n%s' % confirm_link
        r = task.delay(to, title, msg)
        return not r.failed()


class Storage(models.Model):
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='storages')
    key = models.CharField(max_length=16, blank=True, null=True, default=None)
    value = JSONField(blank=True, null=True, default=None, db_index=False)

    class Meta:
        unique_together = ('vd', 'key',)


class Tracking(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

    def __unicode__(self):
        return "VD(id=%d)'s Tracking(lat=%0.6f, lon=%0.6f)" % (self.vd_id, self.lonLat.y, self.lonLat.x)

    @classmethod
    def create(cls, vd_id, lonLat, timestamp=None):
        from uuid import UUID
        if not vd_id:
            raise ValueError
        if not timestamp:
            timestamp = get_timestamp()
        # TODO : 남은 하위 2byte 활용
        hstr = hex((vd_id << 10*8) | (timestamp << 2*8) | 0)[2:-1]     # 끝에 붙는 L 을 떼내기 위해 -1
        _id = UUID(hstr.rjust(32, b'0'))
        instance = Tracking.objects.create(id=_id, lonLat=lonLat)
        return instance

    @property
    def created(self):
        return self.id and (int(self.id) >> 2*8) & BIT_ON_8_BYTE

    @property
    def vd_id(self):
        return self.id and (int(self.id) >> 10*8) & BIT_ON_6_BYTE

    @property
    def vd(self):
        return VD.objects.get(id=self.vd_id)
