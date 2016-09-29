#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from account.models import RealUser
from base.utils import convert_to_json, get_timestamp


class Notice(models.Model):
    created = models.BigIntegerField(blank=True, null=True, default=None)
    title = models.CharField(max_length=254, blank=False, null=False, default=None)
    data = JSONField(blank=True, null=True, default=None, db_index=False)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = get_timestamp()
        self.data = convert_to_json(self.data)
        super(Notice, self).save(*args, **kwargs)


class Inquiry(models.Model):
    created = models.BigIntegerField(blank=True, null=True, default=None)
    ru = models.ForeignKey(RealUser, on_delete=models.SET_DEFAULT, null=False, default=None, related_name='inquiries')
    data = JSONField(blank=True, null=True, default=None, db_index=False)

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = get_timestamp()
        self.data = convert_to_json(self.data)
        super(Inquiry, self).save(*args, **kwargs)
