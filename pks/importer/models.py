#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.db import IntegrityError

from account.models import VD


class Proxy(models.Model):

    id = models.BigIntegerField(primary_key=True, default=None)
    vd = models.OneToOneField(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='proxy')
    guide = JSONField(blank=True, null=True, default=None, db_index=True, unique=True)
    subscribers = models.ManyToManyField(VD, through='Importer', related_name='proxies')

    def __unicode__(self):
        if self.vd:
            return "%s's proxy" % unicode(self.vd)
        return None

    def save(self, *args, **kwargs):
        if not self.vd:
            raise IntegrityError('Proxy.vd must not be None')
        if not self.id:
            self.id = self.vd.id
        super(Proxy, self).save(*args, **kwargs)


class Importer(models.Model):

    publisher = models.ForeignKey(Proxy, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='importers')
    subscriber = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='importers')

    class Meta:
        unique_together = ('subscriber', 'publisher',)
