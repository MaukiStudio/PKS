#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from django.contrib.gis.db import models
from base64 import b16encode
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from cryptography.fernet import Fernet
from requests import post as requests_post
from json import loads as json_loads
from rest_framework import status

from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE, get_uuid_from_ts_vd
from place.post import PostBase
from base.models import Point
from content.models import PlaceName
from base.libs import distance_geography
from pks.settings import VD_ENC_KEY
from base.cache import cache_get_or_create, cache_expire

RADIUS_LOCAL_RANGE = 150


class Place(models.Model):

    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    placeName = models.ForeignKey(PlaceName, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='places')

    def __init__(self, *args, **kwargs):
        self._cache_placePost = None
        super(Place, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.placeName:
            return self.placeName.content
        return 'No named place object'

    def _clearCache(self):
        cache_expire(None, 'placePost_%s' % self.id)
        self._cache_placePost = None

    @property
    def placePost(self):
        def helper(self):
            pb = PostBase()
            for pp in self.pps.all().filter(uplace=None).order_by('id'):
                if pp.is_bounded:
                    continue
                pb_new = pp.pb
                pb.update(pb_new, pp.is_add)
            pb.place_id = self.id
            pb.normalize()
            return pb
        if not self._cache_placePost:
            self._cache_placePost, is_created = cache_get_or_create(None, 'placePost_%s' % self.id, None, helper, self)
        return self._cache_placePost

    @property
    def _totalPost(self):
        pb = PostBase()
        for pp in self.pps.all().order_by('id'):
            pb.update(pp.pb, pp.is_add)
        pb.place_id = self.id
        pb.normalize()
        return pb


    # TODO : 값들이 서로 모순되는 경우에 대한 처리
    # TODO : 추가로 실시간으로 같은 place 를 찾을 수 있는 상황이라면 곧바로 처리
    # TODO : 장소이름만 단독으로 먼저 붙이고, 그 이후에 좌표를 추가하는 경우 현재 장소화가 안됨.
    @classmethod
    def get_or_create_smart(cls, pb, vd):

        #######################################
        # Direct Placed Part
        #######################################

        # place_id 가 명확히 지정된 경우
        if pb.place_id:
            return cls.objects.get(id=pb.place_id), False

        # uplace, lonLat 조회
        uplace = None
        if pb.uplace_uuid:
            uplace = UserPlace.get_from_uuid(pb.uplace_uuid)
        lonLat = pb.lonLat or (uplace and uplace.lonLat)

        # Placed by LegacyPlace
        lp = None
        if pb.lps:
            pb.normalize()
            lp = pb.lps[0]
            if lp.place:
                place = lp.place
                if not place.placeName or not place.lonLat:
                    if pb.name and pb.lonLat:
                        place.placeName = pb.name
                        place.lonLat = pb.lonLat
                        place.save()
                        PostPiece.create_smart_4place(place, vd, pb)
                return place, False

        # Placed by placeName/lonLat
        placeName = pb.name
        if placeName and lonLat:
            qs = Place.objects.filter(placeName=placeName)\
                .filter(lonLat__distance_lte=(lonLat, D(m=RADIUS_LOCAL_RANGE)))\
                .annotate(distance=Distance('lonLat', lonLat)).order_by('distance')
            if qs and qs[0]:
                _place = qs[0]
                # TODO : 리팩토링 필요
                if lp:
                    lp.place = _place
                    lp.save()
                    PostPiece.create_smart_4place(_place, vd, pb)
                return _place, False


        #######################################
        # Indirect Placed Part
        #######################################

        # Placed by LegacyPlace
        if lp:
            _place = Place.objects.create(lonLat=lonLat, placeName=placeName)
            lp.place = _place
            lp.save()
            PostPiece.create_smart_4place(_place, vd, pb)
            return _place, True

        # Placed by placeName/lonLat
        if placeName and lonLat:
            if not pb.lonLat:
                pb.point = Point(lonLat)
            _place = Place.objects.create(lonLat=lonLat, placeName=placeName)
            PostPiece.create_smart_4place(_place, vd, pb)
            return _place, True

        # last : old_place
        if uplace:
            return uplace.place, False

        return None, False


    @property
    def lonLat_json(self):
        return Point(self.lonLat).json


class UserPlace(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    modified = models.BigIntegerField(blank=True, null=True, default=None)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    mask = models.SmallIntegerField(blank=True, null=True, default=None)

    parent = models.ForeignKey('self', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='childs')
    shorten_url = models.CharField(max_length=254, blank=True, null=True, default=None)

    def __init__(self, *args, **kwargs):
        self._cache_userPost = None
        self._cache_total_pps = None
        self._cache_prev_tags = None
        self._cache_prev_NLL = None
        self._cache_vd_ids = None
        self._origin = None
        self._search_tags = None
        super(UserPlace, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.place and self.place.placeName:
            return self.place.placeName.content
        return 'No named uplace object'

    @property
    def uuid(self):
        return '%s.%s' % (b16encode(self.id.bytes), 'uplace',)

    @classmethod
    def get_from_uuid(cls, _uuid):
        splits = _uuid.split('.')
        if splits[1] not in ('uplace', 'iplace'):
            raise ValueError
        _id = UUID(splits[0])
        return cls.objects.get(id=_id)

    def placed(self, place, lonLat=None):
        self.place = place
        self.lonLat = lonLat or place.lonLat or self.lonLat
        self.save()
        for pp in self.pps.all():
            pp.place = place
            pp.save()

    @classmethod
    def get_or_create_smart(cls, pb, vd):
        place, is_created = Place.get_or_create_smart(pb, vd)
        uplace = None
        is_uplace_created = False

        # TODO : uplace 좀 더 찾기...
        if pb.uplace_uuid:
            uplace = cls.get_from_uuid(pb.uplace_uuid)
        if not uplace and place:
            uplace = UserPlace.objects.filter(vd_id__in=vd.realOwner_vd_ids, place=place).order_by('id').first()

        lonLat = (place and place.lonLat) or pb.lonLat or (uplace and uplace.lonLat)

        # 실시간 장소화
        if not uplace:
            uplace = cls.objects.create(vd=vd, place=place, lonLat=lonLat)
            is_uplace_created = True
        elif not uplace.place:
            if place:
                uplace.placed(place, lonLat)
        else:
            if place and uplace.place != place:
                uplace.placed(place, lonLat)
                # TODO : 로그 남겨서 Place Merge 시 우선순위 높여 참고하기

        # 결과 처리
        pb.place_id = uplace.place_id
        pb.uplace_uuid = uplace.uuid
        return uplace, is_uplace_created

    # TODO : DB 저장 회수 많음. 튜닝 필요
    def get_or_create_child(self, place=None):
        if self.parent:
            print('[Child cannot created from other Child]')
            print('[Child info]')
            self.dump()
            print('[Parent info]')
            self.parent.dump()
            print('------------------------------')
            raise NotImplementedError
        self.is_parent = True
        self.place = None
        self.save()

        pb = PostBase()
        pb.place_id = place and place.id or None
        child, is_created = UserPlace.get_or_create_smart(pb, self.vd)
        # 하기 is_created 에 의한 if 처리는 반드시 해야 함
        # 이를 하지 않으면 생성(U1) --> URL장소화(P1) --> 생성(U2) --> URL장소(P2) 에서 문제 발생
        # 위 문제가 아니더라도 성능상 유리
        if is_created:
            child.parent = self
            child.save()
        return child, is_created

    def process_child(self, place=None):
        if self.is_parent:
            self.get_or_create_child(place)
        else:
            if self.place:
                self.get_or_create_child(self.place)    # 기존 매핑 Place 로도 별도 child 생성
                self.get_or_create_child(place)
            else:
                self.placed(place)

    @property
    def post_cache_name(self):
        return 'userPost_%s' % self.uuid

    def _clearCache(self):
        cache_expire(self.vd, self.post_cache_name)
        self._cache_userPost = None
        self._cache_total_pps = None
        self._cache_prev_tags = None
        self._cache_prev_NLL = None
        self._cache_vd_ids = None
        if self.place:
            self.place._clearCache()

    @property
    def vd_ids(self):
        if self._cache_vd_ids is None:
            self._cache_vd_ids = []
            if self.vd:
                self._cache_vd_ids.extend(self.vd.realOwner_vd_ids)
                self._cache_vd_ids.extend(self.vd.realOwner_publisher_ids)
        return self._cache_vd_ids

    @property
    def base_post(self):
        base_post = self.parent and self.parent.userPost or PostBase()
        # TODO : 아래 코드가 기억나지 않음 ㅠ_ㅜ 정체 파악 후 다시 부활
        #base_post.reset_except_region_property()
        base_post = base_post.copy()
        return base_post

    @property
    def total_pps(self):
        if not self._cache_total_pps:
            if not self.place or self.is_bounded:
                self._cache_total_pps = self.pps.all().order_by('id')
            else:
                qs1 = self.place.pps.filter(vd__in=self.vd_ids)
                uplace_publisher_ids = []
                for pp in qs1:
                    if 'iplace_uuid' in pp.data:
                        from importer.models import ImportedPlace
                        iplace = ImportedPlace.get_from_uuid(pp.data['iplace_uuid'])
                        uplace_publisher_ids.extend(iplace.vd.realOwner_vd_ids)
                if uplace_publisher_ids:
                    qs2 = self.place.pps.filter(vd__in=uplace_publisher_ids)
                    self._cache_total_pps = (qs1 | qs2).order_by('id')
                else:
                    self._cache_total_pps = qs1.order_by('id')
        return self._cache_total_pps

    @property
    def userPost(self):
        def helper(self):
            pb = self.base_post
            for pp in self.total_pps:
                if pp.vd and pp.vd.is_private and pp.vd.id not in self.vd.realOwner_vd_ids and pp.vd.parent.id not in self.vd.realOwner_vd_ids:
                    continue
                if pp.is_bounded:
                    continue
                if pp.is_drop:
                    # TODO : 이 부분이 테스트되는 테스트 추가
                    if pp.vd.id in self.vd.realOwner_vd_ids:
                        pb = self.base_post
                    else:
                        # TODO : 친구는 이 장소를 drop 했으므로... 이를 어떠한 형태로든 userPost 에 반영하기
                        pass
                    pass
                else:
                    pb.update(pp.pb, pp.is_add)
            pb.uplace_uuid = self.uuid
            pb.place_id = self.place_id
            pb.normalize()
            return pb
        if not self._cache_userPost:
            self._cache_userPost, is_created = cache_get_or_create(self.vd, self.post_cache_name, None, helper, self)
            #self._cache_userPost = helper(self)
        return self._cache_userPost

    @property
    def placePost(self):
        return self.place and self.place.placePost or None

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        return get_uuid_from_ts_vd(timestamp, vd_id)

    def save(self, *args, **kwargs):
        self.modified = kwargs.pop('timestamp', get_timestamp())
        if not self.id:
            self.id = self._id(self.modified)
        if not self.lonLat:
            self.lonLat = (self.place and self.place.lonLat) or None
        if not self.mask:
            self.mask = 0
        if self.parent:
            if not self.parent.is_parent:
                self.parent.is_parent = True
                self.parent.save()
        super(UserPlace, self).save(*args, **kwargs)

    @property
    def created(self):
        return self.id and (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    @property
    def lonLat_json(self):
        return Point(self.lonLat).json

    @property
    def is_drop(self):
        return ((self.mask or 0) & 1) != 0
    @is_drop.setter
    def is_drop(self, value):
        if value:
            self.mask = (self.mask or 0) | 1
        else:
            self.mask = (self.mask or 0) & (~1)

    @property
    def is_hard2placed(self):
        return (self.mask or 0) & 2 != 0
    @is_hard2placed.setter
    def is_hard2placed(self, value):
        if value:
            self.mask = (self.mask or 0) | 2
        else:
            self.mask = (self.mask or 0) & (~2)

    @property
    def is_hurry2placed(self):
        return (self.mask or 0) & 4 != 0
    @is_hurry2placed.setter
    def is_hurry2placed(self, value):
        if value:
            self.mask = (self.mask or 0) | 4
        else:
            self.mask = (self.mask or 0) & (~4)

    @property
    def is_parent(self):
        return (self.mask or 0) & 8 != 0
    @is_parent.setter
    def is_parent(self, value):
        if value:
            self.mask = (self.mask or 0) | 8
        else:
            self.mask = (self.mask or 0) & (~8)

    # 비어 있는 uplace
    # 공유용 uplace 를 만들때, 초기 상태를 표현하기 위한 속성
    @property
    def is_empty(self):
        return (self.mask or 0) & 16 != 0
    @is_empty.setter
    def is_empty(self, value):
        if value:
            self.mask = (self.mask or 0) | 16
        else:
            self.mask = (self.mask or 0) & (~16)

    # 자신에게 연결된 pp 만으로 (bounded) post 가 구성되는 uplace 의 경우 True
    # 일시적 공유용 Customized post 를 만들기 위해 활용
    @property
    def is_bounded(self):
        return (self.mask or 0) & 32 != 0
    @is_bounded.setter
    def is_bounded(self, value):
        if value:
            self.mask = (self.mask or 0) | 32
        else:
            self.mask = (self.mask or 0) & (~32)

    @property
    def origin(self):
        return self._origin
    @origin.setter
    def origin(self, value):
        self._origin = value

    @property
    def distance_from_origin(self):
        if not self.origin or not self.lonLat:
            return None
        m = distance_geography(self.origin, self.lonLat)
        m = int(round(m/10.0))*10.0
        if m < 1000.0:
            return '%dm' % m
        k = int(round(m/100.0))/10.0
        return '%.1fkm' % k

    # Negative Log Likelyhood
    # Test in tag/test_models.py
    # TODO : 튜닝
    # P(t1,t2,...,tn | place) = P(t1|place)P(t2|t1,place)...P(tn|t1,t2,...,place)
    def getNLL(self, tags):
        from math import log
        uplace_tags = list(self.tags.all())
        tags_in_utags = [tag for tag in tags if tag in uplace_tags]

        place_tags = []
        ptags = []
        tags_in_ptags = []
        if self.place:
            place_ptags = list(self.place.ptags.all())
            place_tags = [ptag.tag for ptag in place_ptags]
            ptags = [ptag for ptag in place_ptags if ptag.tag in tags and ptag.tag not in tags_in_utags]
            tags_in_ptags = [ptag.tag for ptag in ptags]
        tags_others = list(set([tag for tag in tags if tag not in tags_in_utags and tag not in tags_in_ptags]))

        # utags 는 모두 prob = 1.0 --> NLL = 0.0
        result = 0.0

        # ptags
        for ptag in ptags:
            # place 가 결정되어 있으면 ti, tj (i != j) 는 서로 조건부 독립
            # So P(ti|t1,t2,...,t(i-1),place) = P(ti|place)
            result -= log(ptag.prob)

        # tags_others
        # place 에 해당 tag 들에 대한 정보가 전혀 없다면, place 와 ti 는 서로 독립으로 볼 수 있다???
        # TODO : 맞는지 확인. 왠지 아닌 것 같긴 한데 Naive Bayse 의 조건부독립 근사처럼 근사가 가능할 듯...
        # So P(ti|t1,t2,...,t(i-1),place) = P(ti|t1,t2,...,t(i-1)) if place do not have t1, t2, ..., ti
        for tag in tags_others:
            Ds = list(set(uplace_tags+place_tags))
            # 조건부 독립으로 가정하고 tags_others 의 있는 tag 들을 쪼개어 곱함
            prob = tag.posterior(Ds)
            result -= log(prob)

        return result

    @property
    def search_tags(self):
        return self._search_tags
    @search_tags.setter
    def search_tags(self, value):
        self._search_tags = value

    @property
    def NLL(self):
        if self.search_tags:
            if self._cache_prev_tags == self.search_tags and self._cache_prev_NLL:
                return self._cache_prev_NLL
            self._cache_prev_tags = self.search_tags
            self._cache_prev_NLL = self.getNLL(self.search_tags)
            return self._cache_prev_NLL
        return None

    def dump(self):
        reloaded = self.reload()
        print('----- UserPlace Dump -----')
        print('uuid = %s' % (reloaded.uuid,))
        print('place_id = %s' % (reloaded.place_id,))
        print('is_parent = %s' % reloaded.is_parent)
        print('parent = %s' % (reloaded.parent and reloaded.parent.uuid,))
        print('pps.count() = %s' % (reloaded.pps.count(),))
        print('pps.first().data = %s' % (reloaded.pps.first() and reloaded.pps.first().data,))
        print('')

    def reload(self):
        return UserPlace.objects.get(id=self.id)

    @classmethod
    def dump_all(cls):
        print('[DUMP ALL START]')
        for uplace in cls.objects.all():
            uplace.dump()
        print('[DUMP ALL END]')
        print('')

    @property
    def aid(self):
        encrypter = Fernet(VD_ENC_KEY)
        result = encrypter.encrypt(b16encode(self.id.bytes).encode(encoding='utf-8'))
        return result

    @classmethod
    def aid2id(cls, aid):
        decrypter = Fernet(VD_ENC_KEY)
        result = decrypter.decrypt(aid.encode(encoding='utf-8'))
        return UUID(result)

    @property
    def ui_url(self):
        from pks.settings import SERVER_HOST
        return '%s/ui/diaries/%s/' % (SERVER_HOST, self.aid)

    def make_shorten_url(self, longUrl=None, idx=None):
        if self.shorten_url:
            return self.shorten_url

        headers = {'content-type': 'application/json'}
        from base.google import get_api_key
        api_key = get_api_key(idx)
        api_url = 'https://www.googleapis.com/urlshortener/v1/url?key=%s' % api_key
        if not longUrl:
            longUrl = self.ui_url
        # TODO : 테스트를 위해 거시기한 구조의 구현이 되어 있음. 개선
        longUrl = longUrl.replace('http://192.168.1.2:8000/', 'http://placekoob.com/')
        longUrl = longUrl.replace('http://192.168.1.3:8000/', 'http://placekoob.com/')
        data = '{"longUrl": "%s"}' % longUrl
        try:
            r = requests_post(api_url, headers=headers, data=data, timeout=60)
        except:
            return None
        if not r.status_code == status.HTTP_200_OK:
            return None

        d = json_loads(r.content)
        if not d or 'id' not in d or not d['id']:
            return None

        shorten_url = d['id']
        self.shorten_url = shorten_url
        self.save()
        return shorten_url

    @property
    def wrapping_shorten_url(self):
        if self.shorten_url:
            from pks.settings import SERVER_HOST
            return '%s/g/%s' % (SERVER_HOST, self.shorten_url.split('/')[3])
        return None


class PostPiece(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=None)

    # properties mask
    mask = models.SmallIntegerField(blank=True, null=True, default=None)

    # ref
    uplace = models.ForeignKey(UserPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pps')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pps')

    # MAMMA 등 Machine 이 포스팅한 것은 None 으로 세팅됨
    # 허나 ID 발급을 위해 vd 자체는 세팅해서 넘겨야 한다
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pps')

    # json
    data = JSONField(blank=True, null=True, default=None, db_index=True)

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        return get_uuid_from_ts_vd(timestamp, vd_id)

    def process_tag(self):
        if self.uplace:
            from tag.models import UserPlaceTag
            pb = self.pb
            for placeNote in pb.notes:
                for tag in placeNote.tags.all():
                    uptag, is_created = UserPlaceTag.objects.get_or_create(tag=tag, uplace=self.uplace)

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            self.id = self._id(timestamp)
            self.process_tag()
        if not self.mask:
            self.mask = 0
        if not self.place and (self.uplace and self.uplace.place):
            self.place = self.uplace.place

        # Machine 이 포스팅한 경우 vd를 None 으로. 단, vd값이 넘어온 경우 id값 계산시엔 활용 (위에서 이미 id 계산)
        if self.by_MAMMA:
            self.vd = None
        super(PostPiece, self).save(*args, **kwargs)

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    @property
    def is_remove(self):
        return ((self.mask or 0) & 1) != 0
    @is_remove.setter
    def is_remove(self, value):
        if value:
            self.mask = (self.mask or 0) | 1
        else:
            self.mask = (self.mask or 0) & (~1)

    @property
    def is_add(self):
        return not self.is_remove

    @property
    def by_MAMMA(self):
        return ((self.mask or 0) & 2) != 0
    @by_MAMMA.setter
    def by_MAMMA(self, value):
        if value:
            self.mask = (self.mask or 0) | 2
        else:
            self.mask = (self.mask or 0) & (~2)

    @property
    def is_drop(self):
        return ((self.mask or 0) & 4) != 0
    @is_drop.setter
    def is_drop(self, value):
        if value:
            self.mask = (self.mask or 0) | 4
        else:
            self.mask = (self.mask or 0) & (~4)

    # UserPlace.is_bounded == True 인 uplace 에 의해 활용됨
    @property
    def is_bounded(self):
        return ((self.mask or 0) & 8) != 0
    @is_bounded.setter
    def is_bounded(self, value):
        if value:
            self.mask = (self.mask or 0) | 8
        else:
            self.mask = (self.mask or 0) & (~8)

    @property
    def pb(self):
        vd = None
        if self.uplace:
            vd = self.vd
        pb1 = PostBase(self.data, self.timestamp, vd)
        '''
        if pb1.iplace_uuid and self.uplace:
            from importer.models import ImportedPlace
            iplace = ImportedPlace.get_from_uuid(pb1.iplace_uuid)
            if iplace.id == self.uplace.id:
                return pb1
            if iplace and iplace.vd and not iplace.vd.is_private:
                iplace.subscriber = self.vd
                iplace.is_bounded = True
                post = iplace.userPost
                pb1.update(post)
        '''
        return pb1

    @pb.setter
    def pb(self, value):
        self.data = value.ujson

    @classmethod
    def create_smart(cls, uplace, pb, is_drop=False, is_remove=False):
        MAX_IMG_CNT = 30
        img_cnt = len(pb.images)
        if img_cnt > MAX_IMG_CNT:
            pb_copied = pb.copy()
            pp = None
            for i in xrange((img_cnt+MAX_IMG_CNT-1)/MAX_IMG_CNT):
                start = img_cnt - (i+1)*MAX_IMG_CNT
                if start < 0: start = 0
                end = img_cnt - i*MAX_IMG_CNT
                pb_copied.images = pb.images[start:end]
                pp = PostPiece.objects.create(uplace=uplace, pb=pb_copied, place=uplace.place, vd=uplace.vd,
                                              is_drop=is_drop, is_remove=is_remove, is_bounded=uplace.is_bounded)
        else:
            pp = PostPiece.objects.create(uplace=uplace, pb=pb, place=uplace.place, vd=uplace.vd,
                                          is_drop=is_drop, is_remove=is_remove, is_bounded=uplace.is_bounded)
        return pp

    @classmethod
    def create_smart_4place(cls, place, vd, pb, by_MAMMA=None):
        if by_MAMMA is None:
            by_MAMMA = pb.by_MAMMA
        return PostPiece.objects.create(place=place, vd=vd, pb=pb, by_MAMMA=by_MAMMA, uplace=None)
