#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import sha256
from base64 import urlsafe_b64encode
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import AbstractUser

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

    def __unicode__(self):
        return self.email

    @property
    def vd_ids(self):
        return [vd.id for vd in self.vds.all()]


class VD(models.Model):
    authOwner = models.ForeignKey(User, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='vds')
    realOwner = models.ForeignKey(RealUser, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='vds')

    lastLonLat = models.PointField(blank=True, null=True, default=None)
    data = JSONField(blank=True, null=True, default=None)

    deviceName = models.CharField(max_length=36, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)

    country = models.CharField(max_length=2, blank=True, null=True, default=None)
    language = models.CharField(max_length=2, blank=True, null=True, default=None)
    timezone = models.CharField(max_length=5, blank=True, null=True, default=None)

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
