#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models

from place.models import UserPlace, Place
from content.models import TagName


# TODO : 튜닝 (캐싱 등)
class Tag(models.Model):
    tagName = models.OneToOneField(TagName, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='tag')
    uplaces = models.ManyToManyField(UserPlace, through='UserPlaceTag', related_name='tags')
    places = models.ManyToManyField(Place, through='PlaceTag', related_name='tags')

    def __unicode__(self):
        return unicode(self.tagName)

    def save(self, *args, **kwargs):
        if self.id and self.id <= 0:
            raise NotImplementedError
        super(Tag, self).save(*args, **kwargs)

    @property
    def prior(self):
        return TagMatrix.prior(self)


# TODO : 튜닝, 부동소수점 연산 정확성 향상
class TagMatrix(models.Model):
    row = models.IntegerField(blank=True, null=True, default=None)
    col = models.IntegerField(blank=True, null=True, default=None)
    count = models.IntegerField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('row', 'col')

    def save(self, *args, **kwargs):
        if not (self.row >= 0) or not (self.col >= 0):
            raise NotImplementedError
        if self.row < self.col:
            raise NotImplementedError
        super(TagMatrix, self).save(*args, **kwargs)


    @classmethod
    def row_col(cls, elem1, elem2):
        if type(elem1) is Tag:
            elem1 = elem1.id
        if type(elem2) is Tag:
            elem2 = elem2.id
        return sorted([elem1, elem2], reverse=True)

    @classmethod
    def inc(cls, row, col):
        row, col = TagMatrix.row_col(row, col)
        tm, is_created = cls.objects.get_or_create(row=row, col=col)
        if is_created:
            tm.count = 0
        tm.count += 1
        tm.save()
        return tm.count

    @classmethod
    def inc_places_count(cls):
        tm, is_created = cls.objects.get_or_create(row=0, col=0)
        if is_created:
            tm.count = 0
        tm.count += 1
        tm.save()
        return tm.count

    @classmethod
    def get(cls, row, col):
        row, col = TagMatrix.row_col(row, col)
        try:
            tm = cls.objects.get(row=row, col=col)
        except TagMatrix.DoesNotExist:
            tm = TagMatrix(row=row, col=col, count=0)
        return tm.count

    @classmethod
    def places_count(cls):
        return cls.get(0, 0)

    @classmethod
    def prior(cls, T):
        total = TagMatrix.places_count()
        if total <= 0:
            return 0.5
        T_total = TagMatrix.get(T, T)
        result = (float(T_total)+0.5) / (float(total)+1.0)
        return result

    @classmethod
    def likelyhood(cls, D, H):
        if D == H:
            return 1.0
        H_total = TagMatrix.get(H, H)
        prior_D = TagMatrix.prior(D)
        if H_total <= 0:
            return prior_D
        intersection = TagMatrix.get(D, H)
        result = (float(intersection)+prior_D) / (float(H_total)+1.0)
        return result


class UserPlaceTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uptags')
    uplace = models.ForeignKey(UserPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uptags')
    created = models.BigIntegerField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('tag', 'uplace')

    def __unicode__(self):
        return self.tag and unicode(self.tag) or None


    def save(self, *args, **kwargs):
        if self.id:
            raise NotImplementedError
        if self.uplace and self.uplace.place:
            self.process_tag()
        super(UserPlaceTag, self).save(*args, **kwargs)

    def process_tag(self):
        if self.tag and self.uplace and self.uplace.place:
            place = self.uplace.place
            ptag, is_created = PlaceTag.objects.get_or_create(tag=self.tag, place=place)
            if is_created:
                tags = place.tags.all()
                for tag in tags:
                    TagMatrix.inc(self.tag, tag)
                if len(tags) == 1:
                    TagMatrix.inc_places_count()


class PlaceTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ptags')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ptags')
    created = models.BigIntegerField(blank=True, null=True, default=None)
    prob = models.FloatField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('tag', 'place')

    def __unicode__(self):
        return self.tag and unicode(self.tag) or None

    def delete(self, using=None, keep_parents=False):
        # 삭제하지 말고 prob 을 조정할 것
        raise NotImplementedError
