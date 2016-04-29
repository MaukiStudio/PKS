#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from account.models import VD


'''
class Importer(models.Model):

    source = models.OneToOneField(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='importer')
    source_data = JSONField(blank=True, null=True, default=None, db_index=True)
    targets = models.ManyToManyField(VD, through='UserImporter', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='importers')
    timestamp = models.BigIntegerField(blank=True, null=True, default=None)


class UserImporter(models.Model):

    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uimporters')
    importer = models.ForeignKey(Importer, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uimporters')
    timestamp = models.BigIntegerField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('vd', 'importer',)
'''
