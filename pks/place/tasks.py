#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from place.models import PostBase, Place, PostPiece
from content.models import LegacyPlace

class PlaceTask(object):

    def run(self, place_id):
        place = Place.objects.get(id=place_id)
        if not place.uplaces.first():
            return False
        uplace = place.uplaces.first()
        post = place.placePost

        place.placeName = place.placeName or post.name
        place.lonLat = place.lonLat or post.lonLat
        if not place.placeName or not place.lonLat:
            return False
        place.save()
        name = place.placeName.content
        lon = place.lonLat.x
        lat = place.lonLat.y

        # 일단 LegacyPlace 에 의한 장소화가 되지 않은 경우만 구글 호출
        # TODO : 구글 장소화는 무조건 시도하고... 구글에 없는 경우 구글 DB 에 추가
        if not place.lps.first():
            if place.placeName and place.lonLat:
                google_place_id = LegacyPlace.find_google_place_id_by_lonLatName(name, lon, lat)
                if google_place_id:
                    lp, is_created = LegacyPlace.get_or_create_smart('%s.google' % google_place_id)
                    if not lp.place:
                        lp.place = place
                        lp.save()
                    pb = PostBase()
                    pb.lps.append(lp)
                    PostPiece.create_smart_4place(place, uplace.vd, pb.pb_MAMMA)
                    return True

        return False
