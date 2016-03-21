#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import sha256
from base64 import urlsafe_b64encode
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User

from cryptography.fernet import Fernet
from pks.settings import VD_ENC_KEY


class RealUser(models.Model):
    email = models.EmailField(unique=True, blank=False, null=False, default=None)

    def __str__(self):
        return self.email


class VD(models.Model):
    authOwner = models.ForeignKey(User, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='vds')
    realOwner = models.ForeignKey(RealUser, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='vds')

    lastLonLat = models.PointField(blank=True, null=True, default=None)
    data = JSONField(blank=True, null=True, default=None)

    deviceName = models.CharField(max_length=36, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)

    def __str__(self):
        email = (self.realOwner and self.realOwner.email) or (self.authOwner and self.authOwner.email) or 'unknown@email'
        deviceTypeName = self.deviceTypeName or 'unknown device'
        deviceNameCaption = (self.deviceName and ' (%s)' % self.deviceName) or ''
        return '%s\'s %s%s' % (email, deviceTypeName, deviceNameCaption)

    @property
    def _encKey(self):
        if self.authOwner is None:
            return VD_ENC_KEY
        raw_key = '%d|%s' % (self.authOwner.pk, VD_ENC_KEY)
        h = sha256()
        h.update(raw_key)
        return urlsafe_b64encode(h.digest())

    @property
    def _aid(self):
        encrypter = Fernet(self._encKey)
        return encrypter.encrypt(str(self.id).encode(encoding='utf-8'))

    def getIdFromAid(self, aid):
        decrypter = Fernet(self._encKey)
        return int(decrypter.decrypt(aid))

