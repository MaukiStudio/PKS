#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField

from place.models import UserPlace, Place
from content.models import TagName, PlaceNote
from image.models import Image

# For Laplace Smoothing
ALPHA = 0.5

# Tag
TAGGER_AZURE = 'A'
TAG_JSON_NAME = 'T'

# Tag Prob
TAG_MIN_PROB = 0.05


# TODO : 튜닝 (캐싱 등)
class Tag(models.Model):
    tagName = models.OneToOneField(TagName, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='tag')
    uplaces = models.ManyToManyField(UserPlace, through='UserPlaceTag', related_name='tags')
    places = models.ManyToManyField(Place, through='PlaceTag', related_name='tags')
    placeNotes = models.ManyToManyField(PlaceNote, through='PlaceNoteTag', related_name='tags')

    def __unicode__(self):
        return unicode(self.tagName)

    def save(self, *args, **kwargs):
        if self.id and self.id <= 0:
            raise NotImplementedError
        super(Tag, self).save(*args, **kwargs)

    @classmethod
    def get_or_create_smart(cls, rawTagName):
        tagName, is_tagName_created = TagName.get_or_create_smart(rawTagName)
        instance, is_created = cls.objects.get_or_create(tagName=tagName)
        return instance, is_created

    @property
    def prior(self):
        return TagMatrix.prior(self)

    def likelyhood(self, D):
        return TagMatrix.likelyhood(D, self)

    def likelyhood_negation(self, D):
        return TagMatrix.likelyhood_negation(D, self)

    def posterior(self, Ds):
        positive = self.prior
        negative = 1 - positive
        for D in Ds:
            if D == self:
                raise NotImplementedError
            positive *= self.likelyhood(D)
            negative *= self.likelyhood_negation(D)
        result = positive / (positive + negative)
        return result

    @classmethod
    def tags_from_note(cls, note):
        tags = list()
        note_content = note.content
        if note_content.startswith('[NOTE_TAGS]#'):
            json = json_loads(note_content.split('#')[1])
            for rawTagName in json:
                tag, is_created = Tag.get_or_create_smart(rawTagName)
                tags.append(tag)
        else:
            str = note_content.replace(',', ' ')
            for splitted in str.split(' '):
                if splitted.startswith('#'):
                    for rawTagName in splitted.split('#'):
                        if rawTagName:
                            tag, is_created = Tag.get_or_create_smart(rawTagName)
                            tags.append(tag)
        return tags

    @classmethod
    def tags_from_param(cls, param):
        tags = list()
        str = param.replace('#', ',')
        for splitted in str.split(','):
            rawTagName = splitted.replace(' ', '')   # 의도한 것
            if rawTagName:
                tag, is_created = Tag.get_or_create_smart(rawTagName)
                tags.append(tag)
        return tags

    @property
    def json(self):
        return self.tagName.json
    @property
    def cjson(self):
        return self.tagName.cjson
    @property
    def ujson(self):
        return self.tagName.ujson

    @property
    def is_remove(self):
        return self.tagName.is_remove

    @property
    def remove_target(self):
        tagName = self.tagName.remove_target
        if not tagName or not tagName.content:
            return None
        result, is_created = self.get_or_create_smart(tagName.content)
        return result

    @property
    def content(self):
        return self.tagName.content


# TODO : 튜닝, 부동소수점 연산 정확성 향상
# TODO : prior, likelyhood 계산방식, 베이지안 업데이트 방식으로 변경 (unknown 이 너무 많아 이게 더 낫다고 판단)
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
        T_total += (total-T_total)*0.5
        result = (T_total+ALPHA*2) / (total+ALPHA*4)
        return result

    @classmethod
    def likelyhood(cls, D, H):
        if D == H:
            #return 1.0
            raise NotImplementedError
        H_total = TagMatrix.get(H, H)
        if H_total <= 0:
            #return TagMatrix.prior(D)
            #raise NotImplementedError
            return 0.5
        intersection = TagMatrix.get(D, H)
        intersection += (H_total-intersection)*0.5
        result = (intersection+ALPHA) / (H_total+ALPHA*2)
        return result

    @classmethod
    def likelyhood_negation(cls, D, H):
        if D == H:
            #return 0.0
            raise NotImplementedError
        likelyhood = cls.likelyhood(H, D)
        prior_H = cls.prior(H)
        prior_D = cls.prior(D)
        result = (1.0-likelyhood) * prior_D / (1-prior_H)
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
            if self.uplace and self.uplace.vd:
                error_tagging_ratio = self.uplace.vd.error_tagging_ratio
                H = ptag.prob
                ptag.prob = H / (H + error_tagging_ratio*(1-H))
                ptag.save()


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

    def save(self, *args, **kwargs):
        if not self.prob:
            self.prob = 0.5
        super(PlaceTag, self).save(*args, **kwargs)


class PlaceNoteTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ctags')
    placeNote = models.ForeignKey(PlaceNote, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ctags')

    class Meta:
        unique_together = ('tag', 'placeNote')

    def __unicode__(self):
        return self.tag and unicode(self.tag) or None


class ImageTags(models.Model):
    img = models.OneToOneField(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ctags')
    tags = JSONField(blank=True, null=True, default=None, db_index=False)

    def add_tag(self, name, prob, tagger):
        if prob < TAG_MIN_PROB:
            return
        if self.tags is None:
            self.tags = list()
        name = name.lower()
        tag, is_created = Tag.get_or_create_smart(name)
        tag = tag.id

        item = None
        for d in self.tags:
            if TAG_JSON_NAME in d and d[TAG_JSON_NAME] == tag:
                item = d
                break
        if not item:
            item = {TAG_JSON_NAME: tag, TAGGER_AZURE: 0.0}
            self.tags.append(item)

        # TODO : 현재는 MAX 인데... 더 좋은 로직 고민
        item[tagger] = max(item['A'], prob)

    def process_azure_tag(self, azure):
        if not azure or not azure.result_analyze:
            return None
        ar = azure.result_analyze

        # description
        if 'description' in ar:
            description = ar['description']
            for name in description['tags']:
                for caption in description['captions']:
                    if name in caption['text']:
                        self.add_tag(name, caption['confidence'], TAGGER_AZURE)

        # adult, racy
        if 'adult' in ar:
            self.add_tag('adult', ar['adult']['adultScore'], TAGGER_AZURE)
            self.add_tag('racy', ar['adult']['racyScore'], TAGGER_AZURE)

        # tags
        if 'tags' in ar:
            for d in ar['tags']:
                name = d['name']
                prob = d['confidence']
                self.add_tag(name, prob, TAGGER_AZURE)
                if 'hint' in d:
                    name = d['hint']
                    self.add_tag(name, prob, TAGGER_AZURE)

        # categories
        if 'categories' in ar:
            for d in ar['categories']:
                names = d['name']
                prob = d['score']
                for name in names.split('_'):
                    if name:
                        self.add_tag(name, prob, TAGGER_AZURE)
                # celebrities
                if 'detail' in d:
                    if 'celebrities' in d['detail']:
                        for celebrity in d['detail']['celebrities']:
                            prob = celebrity['confidence']
                            name = celebrity['name']
                            self.add_tag(name, prob, TAGGER_AZURE)

        # imageType
        if 'imageType' in ar:
            CLIPART_TAGS = ['Non-clipart', 'ambiguous-clipart', 'normal-clipart', 'good-clipart']
            LINEDRAWING_TAGS = ['Non-LineDrawing', 'LineDrawing']
            clipArtType = ar['imageType']['clipArtType']
            lineDrawingType = ar['imageType']['lineDrawingType']
            self.add_tag(CLIPART_TAGS[clipArtType], 0.5, TAGGER_AZURE)
            self.add_tag(LINEDRAWING_TAGS[lineDrawingType], 0.5, TAGGER_AZURE)

        # faces
        if 'faces' in ar:
            for face in ar['faces']:
                gender = face['gender']
                age = face['age']
                self.add_tag(gender, 0.5, TAGGER_AZURE)
                self.add_tag('age_%d' % age, 0.5, TAGGER_AZURE)

    @property
    def tagNames(self):
        result = list()
        for tag_json in self.tags:
            tag = Tag.objects.get(id=tag_json[TAG_JSON_NAME])
            result.append({TAG_JSON_NAME: tag.content, TAGGER_AZURE: tag_json[TAGGER_AZURE]})
        return result

    def dump(self):
        print('')
        print('dump tags of %s' % self.img)
        for tagName in self.tagNames:
            print('%s: %s=%0.4f' % (tagName[TAG_JSON_NAME], TAGGER_AZURE, tagName[TAGGER_AZURE]))
        print('')
