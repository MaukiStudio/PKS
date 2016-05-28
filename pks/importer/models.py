#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.db import IntegrityError
from json import loads as json_loads

from account.models import VD, RealUser
from place.models import UserPlace


class Proxy(models.Model):

    id = models.BigIntegerField(primary_key=True, default=None)
    vd = models.OneToOneField(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='proxy')
    guide = JSONField(blank=True, null=True, default=None, db_index=True, unique=True)
    subscribers = models.ManyToManyField(VD, through='Importer', related_name='proxies')
    started = models.BigIntegerField(blank=True, null=True, default=None)
    ended = models.BigIntegerField(blank=True, null=True, default=None)

    def __unicode__(self):
        if self.vd:
            return "%s's proxy" % unicode(self.vd)
        return None

    def save(self, *args, **kwargs):
        if not self.vd:
            raise IntegrityError('Proxy.vd must not be None')
        if not self.id:
            # 나중에 vd 가 바뀔 수 있으며, 이때부터 proxy.id != proxy.vd.id
            self.id = self.vd.id
        if self.guide and type(self.guide) is not dict:
            self.guide = json_loads(self.guide)
        super(Proxy, self).save(*args, **kwargs)

    def reload(self):
        return Proxy.objects.get(id=self.id)

    # TODO : priority 처리 구현
    def start(self, high_priority=False):
        from importer.task_wrappers import ProxyTaskWrapper
        task = ProxyTaskWrapper()
        r = task.delay(self.id)

        # TODO : 정확한 구현인지 확인
        if r.failed():
            raise NotImplementedError
        return r

    @property
    def vd_ids(self):
        if self.guide and 'type' in self.guide and self.guide['type'] == 'user':
            ru = RealUser.objects.get(email=self.guide['email'])
            return ru.vd_ids
        return [self.vd_id]


class Importer(models.Model):

    publisher = models.ForeignKey(Proxy, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='importers')
    subscriber = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='importers')
    started = models.BigIntegerField(blank=True, null=True, default=None)
    ended = models.BigIntegerField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('subscriber', 'publisher',)

    def save(self, *args, **kwargs):
        if not self.publisher or not self.subscriber:
            raise IntegrityError('Importer.publisher and subscriber must not be None')
        super(Importer, self).save(*args, **kwargs)

    def reload(self):
        return Importer.objects.get(id=self.id)

    # TODO : priority 처리 구현
    def start(self, high_priority=False):
        from importer.task_wrappers import ImporterTaskWrapper
        task = ImporterTaskWrapper()
        r = task.delay(self.id)

        # TODO : 정확한 구현인지 확인
        if r.failed():
            raise NotImplementedError
        return r


# 일단 iplace 는 별도 저장하지 않고 uplace 에서 조회하여 사용 : So Proxy Model
# 향후 성능을 위해 별도 저장할 수도 있음
class ImportedPlace(UserPlace):
    class Meta:
        proxy = True

    def computePost(self, vd_ids=None):
        if self.place:
            self.place.computePost(vd_ids)
        super(ImportedPlace, self).computePost(None)

    @property
    def userPost(self):
        if self.place:
            return self.place.userPost
        return super(ImportedPlace, self).userPost
