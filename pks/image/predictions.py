#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from image.models import Image


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
