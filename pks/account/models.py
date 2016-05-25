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

    deviceName = models.CharField(max_length=36, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)

    country = models.CharField(max_length=2, blank=True, null=True, default=None)
    language = models.CharField(max_length=2, blank=True, null=True, default=None)
    timezone = models.CharField(max_length=5, blank=True, null=True, default=None)

    parent = models.ForeignKey('self', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='childs')
    mask = models.SmallIntegerField(blank=True, null=True, default=None)

    def __init__(self, *args, **kwargs):
        self._cache_realOwner_publisher_ids = None
        self._cache_realOwner_places = None
        self._cache_realOwner_duplicated_uplace_ids = None
        self._cache_realOwner_duplicated_iplace_ids = None
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
            return self.realOwner.vd_ids
        return [self.id]

    # TODO : 캐싱 처리에 용이하도록 리팩토링 및 캐싱
    @property
    def realOwner_publisher_ids(self):
        if not self._cache_realOwner_publisher_ids:
            from importer.models import Importer
            importers = Importer.objects.filter(subscriber_id__in=self.realOwner_vd_ids)
            if importers:
                self._cache_realOwner_publisher_ids = sum([importer.publisher.vd_ids for importer in importers], [])
            else:
                self._cache_realOwner_publisher_ids = []
        return self._cache_realOwner_publisher_ids

    # TODO : 튜닝
    @property
    def realOwner_places(self):
        if not self._cache_realOwner_places:
            from place.models import Place
            self._cache_realOwner_places = Place.objects.filter(uplaces__vd_id__in=self.realOwner_vd_ids)
        return self._cache_realOwner_places

    # TODO : 튜닝!!!
    @property
    def realOwner_duplicated_uplace_ids(self):
        if not self._cache_realOwner_duplicated_uplace_ids:
            from place.models import UserPlace
            base = UserPlace.objects.all().exclude(place_id=None).filter(vd_id__in=self.realOwner_vd_ids)
            group_by = base.values('place_id').annotate(cnt=Count(1)).filter(cnt__gte=2)
            result = list()
            before = None
            for uplace in base.filter(place_id__in=[row['place_id'] for row in group_by]).order_by('place_id', '-id'):
                if uplace.place_id == (before and before.place_id):
                    result.append(uplace.id)
                before = uplace
            self._cache_realOwner_duplicated_uplace_ids = result
        return self._cache_realOwner_duplicated_uplace_ids

    # TODO : 튜닝!!!
    @property
    def realOwner_duplicated_iplace_ids(self):
        if not self._cache_realOwner_duplicated_iplace_ids:
            from importer.models import ImportedPlace
            base = ImportedPlace.objects.all().exclude(place_id=None).filter(vd_id__in=self.realOwner_publisher_ids)
            group_by = base.values('place_id').annotate(cnt=Count(1)).filter(cnt__gte=2)
            result = list()
            before = None
            for iplace in base.filter(place_id__in=[row['place_id'] for row in group_by]).order_by('place_id', '-id'):
                if iplace.place_id == (before and before.place_id):
                    result.append(iplace.id)
                before = iplace
            self._cache_realOwner_duplicated_iplace_ids = result
        return self._cache_realOwner_duplicated_iplace_ids

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
        super(VD, self).save(*args, **kwargs)


class Storage(models.Model):
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='storages')
    key = models.CharField(max_length=16, blank=True, null=True, default=None)
    value = JSONField(blank=True, null=True, default=None, db_index=False)

    class Meta:
        unique_together = ('vd', 'key',)
