#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads, dumps as json_dumps

# stxt_type
STXT_TYPE_PLACE_NOTE = 1
STXT_TYPE_PLACE_NAME = 2
STXT_TYPE_POS_DESC = 3
STXT_TYPE_IMAGE_NOTE = 4
STXT_TYPE_ADDRESS = 5
STXT_TYPE_REMOVE_CONTENT = 254


# TODO : 향후 삭제 처리 구현 필요. 특정 Content 를 삭제하고 싶은 경우 노트타입을 삭제로 붙임. 이 노트타입은 노트뿐만 아니라 다른 Content 에도 적용
class Post(object):

    def __init__(self, value=None):
        t = type(value)
        if t is int or t is long:
            self.json = dict(place_id=value, lonLat=None, images=list(), urls=list(), lps=list(),
                             name=None, notes=list(), posDesc=None, addrs=list(), phone=None,)
            self._json_str = None
        elif t is unicode or t is str:
            self._json_str = value
            self.json = json_loads(value)
        elif t is dict:
            self.json = value
            self._json_str = None
        else:
            raise NotImplementedError

    @property
    def json_str(self):
        if not self._json_str:
            self._json_str = json_dumps(self.json)
        return self._json_str

    def add_pc(self, pc):
        if pc.lonLat and not self.json['lonLat']:
            self.json['lonLat'] = dict(lon=pc.lonLat.x, lat=pc.lonLat.y, timestamp=pc.timestamp)

        if pc.image:
            uuid = pc.image.uuid
            dl = self.json['images']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.image.content, note=None, timestamp=pc.timestamp, summary=pc.image.url_summarized))
            if pc.stxt_type == STXT_TYPE_IMAGE_NOTE and pc.stxt.content:
                d = None
                for dt in dl:
                    if dt['uuid'] == uuid:
                        d = dt
                        break
                if d and not d['note']:
                    d['note'] = dict(uuid=pc.stxt.uuid, content=pc.stxt.content, timestamp=pc.timestamp)

        if pc.url:
            uuid = pc.url.uuid
            dl = self.json['urls']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.url.content, timestamp=pc.timestamp))

        if pc.lp:
            uuid = pc.lp.uuid
            dl = self.json['lps']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.lp.content, timestamp=pc.timestamp))

        if pc.phone and not self.json['phone']:
            self.json['phone'] = dict(uuid=pc.phone.uuid, content=pc.phone.content, timestamp=pc.timestamp)

        if pc.stxt:
            uuid = pc.stxt.uuid
            if pc.stxt_type == STXT_TYPE_PLACE_NAME:
                if not self.json['name']:
                    self.json['name'] = dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp)
            elif pc.stxt_type == STXT_TYPE_PLACE_NOTE:
                dl = self.json['notes']
                if uuid not in [d['uuid'] for d in dl]:
                    dl.append(dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp))
            elif pc.stxt_type == STXT_TYPE_POS_DESC:
                if not self.json['posDesc']:
                    self.json['posDesc'] = dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp)
            elif pc.stxt_type == STXT_TYPE_ADDRESS:
                dl = self.json['addrs']
                if len(dl) <= 2 and uuid not in [d['uuid'] for d in dl]:
                    dl.append(dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp))
            elif pc.stxt_type == STXT_TYPE_IMAGE_NOTE or pc.stxt_type is None:
                pass
            else:
                print(pc.stxt_type)
                raise NotImplementedError


    def isSubsetOf(self, other):
        def isSubsetOf_dict(d1, d2):
            if not d1: return True
            elif not d2: return False
            elif type(d2) is not dict: return False

            for key, value in d1.iteritems():
                if not value:
                    continue
                elif type(value) is dict:
                    if key not in d2 or not isSubsetOf_dict(value, d2[key]):
                        return False
                elif type(value) is list:
                    if key not in d2 or not isSubsetOf_list(value, d2[key]):
                        return False
                else:
                    if key not in d2 or value != d2[key]:
                        return False
            return True
        def isSubsetOf_list(l1, l2):
            if not l1: return True
            elif not l2: return False
            elif type(l2) is not list: return False
            elif len(l1) != len(l2): return False

            for key, value in enumerate(l1):
                if not value:
                    if l2[key]:
                        return False
                elif type(value) is dict:
                    if not isSubsetOf_dict(value, l2[key]):
                        return False
                elif type(value) is list:
                    if not isSubsetOf_list(value, l2[key]):
                        return False
                else:
                    if value != l2[key]:
                        return False
            return True
        return isSubsetOf_dict(self.json, other.json)

    # TODO : 미구현 상태. 구현해야 함
    @property
    def is_valid(self):
        return True


