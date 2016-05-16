#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse
from re import compile as re_compile

from place.models import UserPlace, Place
from account.models import VD
from pks.settings import VD_SESSION_KEY
from place.post import PostBase
from geopy.geocoders import Nominatim

geolocator = Nominatim()


def get_map_url(lonLat):
    map_url = None
    if lonLat:
        # for 튜닝 : 한국이 확실한 경우 geolocator 를 쓰지 않고 곧바로 처리
        if lonLat.y >= 34.0 and lonLat.y <= 39.0 and lonLat.x >= 125.0 and lonLat.x <= 130.0:
            map_url = 'http://map.naver.com/?dlevel=13&x=%f&y=%f' % (lonLat.x, lonLat.y)
        else:
            try:
                location = geolocator.reverse((lonLat.y, lonLat.x))
                if location.raw and 'address' in location.raw and 'country_code' in location.raw['address']:
                    if location.raw['address']['country_code'] == 'kr':
                        map_url = 'http://map.naver.com/?dlevel=13&x=%f&y=%f' % (lonLat.x, lonLat.y)
            except:
                print('geolocator(Nominatim) fail() : lat=%f, lon=%f' % (lonLat.y, lonLat.x))
        if not map_url:
            map_url = 'http://maps.google.com/?q=%f,%f&z=15' % (lonLat.y, lonLat.x)
    return map_url or 'http://map.naver.com/'


def index(request):
    user = request.user
    if user.is_authenticated and user.is_active and user.is_staff:
        vd = user.vds.filter(deviceTypeName='ADMIN').order_by('-id')[0]
        request.session[VD_SESSION_KEY] = vd.id
        return render(request, 'admin2/index.html')
    return redirect('/admin/login/?next=/admin2/')


def placed(request):
    pbs = [uplace.userPost for uplace in UserPlace.objects.filter(place=None).order_by('-id')[:100]]
    for pb in pbs:
        if pb and pb.images:
            for image in pb.images:
                image.summarize()
        pb.map_url = get_map_url(pb.lonLat)
    context = dict(pbs=pbs)
    return render(request, 'admin2/placed.html', context)


def places(request):
    pbs = [place._totalPost for place in Place.objects.order_by('-id')[:100]]
    for pb in pbs:
        if pb and pb.images:
            for image in pb.images:
                image.summarize()
        if pb and pb.points:
            for point in pb.points:
                pb.point.map_url = get_map_url(pb.point.lonLat)
    context = dict(pbs=pbs)
    return render(request, 'admin2/places.html', context)


# TODO : 완전 리팩토링 필요;;; 일단 임시 땜빵임
def placed_detail(request, uplace_id):
    if request.method == 'POST':
        vd = VD.objects.get(id=request.session[VD_SESSION_KEY])

        # LegacyPlace URL 로 장소화
        if 'url' in request.POST and request.POST['url']:
            url = request.POST['url']
            if url in ('삭제', '제거', 'delete','remove'):
                uplace = UserPlace.objects.get(id=uplace_id)
                uplace.delete()
                return redirect('/admin2/placed/%s.uplace/' % uplace_id)

            # PostBase instance 생성
            json_add = '{"urls": [{"content": "%s"}]}' % url
            pb = PostBase(json_add)
            pb.uplace_uuid = '%s.uplace' % uplace_id

            # UserPlace/Place 찾기
            uplace, is_created = UserPlace.get_or_create_smart(pb, vd)
            pb.uplace_uuid = uplace.uuid

            # valid check
            if not pb.is_valid(uplace):
                raise ValueError('PostPiece 생성을 위한 최소한의 정보도 없음')

            pb_MAMMA = pb.pb_MAMMA
            if pb_MAMMA:
                uplace, is_created = UserPlace.get_or_create_smart(pb_MAMMA, vd)

            # redirect
            return redirect('/admin2/placed/%s.uplace/' % uplace_id)

        # placeName/lonLat 로 장소화
        elif 'placeName' in request.POST and request.POST['placeName']:
            placeName = request.POST['placeName']
            lon = None
            lat = None
            if 'lonLat' in request.POST and request.POST['lonLat']:
                raw_lonLat = request.POST['lonLat']
                regexs = [
                    re_compile(r'^.*[&\?]?lat=(?P<lat>[0-9\.]+)&lng=(?P<lon>[0-9\.]+)&?.*$'),
                    re_compile(r'^.*[&\?]?lng=(?P<lon>[0-9\.]+)&lat=(?P<lat>[0-9\.]+)&?.*$'),
                    re_compile(r'^.*[&\?]?lat=(?P<lat>[0-9\.]+)&lon=(?P<lon>[0-9\.]+)&?.*$'),
                    re_compile(r'^.*[&\?]?lon=(?P<lon>[0-9\.]+)&lat=(?P<lat>[0-9\.]+)&?.*$'),
                    re_compile(r'^.*[&\?]?x=(?P<lon>[0-9\.]+)&y=(?P<lat>[0-9\.]+)&?.*$'),
                    re_compile(r'^https.+\.google\..+map.+@(?P<lat>[0-9\.]+),(?P<lon>[0-9\.]+),[0-9]+z.*$'),
                ]
                for regex in regexs:
                    searcher = regex.search(raw_lonLat)
                    if searcher:
                        lon = float(searcher.group('lon'))
                        lat = float(searcher.group('lat'))
                        print('lon', searcher.group('lon'))
                        print('lat', searcher.group('lat'))
                        break
            if not lon or not lat:
                _uplace = UserPlace.objects.get(id=uplace_id)
                if _uplace and _uplace.lonLat:
                    lon = _uplace.lonLat.x
                    lat = _uplace.lonLat.y
            if not lon or not lat:
                # 현재는 이름과 함께 좌표(위도경도)를 넣어줘야 장소화가 됨 (향후 좌표 대신 주소도 가능)
                raise NotImplementedError

            # PostBase instance 생성
            json_add = '{"lonLat": {"lon": %f, "lat": %f}, "name": {"content": "%s"}}' % (lon, lat, placeName,)
            pb = PostBase(json_add)
            pb.uplace_uuid = '%s.uplace' % uplace_id

            # 장소화
            uplace, is_created = UserPlace.get_or_create_smart(pb, vd)

            # redirect
            return redirect('/admin2/placed/%s.uplace/' % uplace_id)

    try:
        uplace = UserPlace.objects.get(id=uplace_id)
    except UserPlace.DoesNotExist:
        return HttpResponse('삭제되었습니다')

    default_lonLat = 'LonLat Required'
    if uplace.lonLat:
        default_lonLat = 'lon=%f&lat=%f' % (uplace.lonLat.x, uplace.lonLat.y)
    uplace.userPost.map_url = get_map_url(uplace.lonLat)
    if uplace.placePost:
        uplace.placePost.map_url = get_map_url(uplace.placePost.lonLat)
    context = dict(userPost=uplace.userPost, placePost=uplace.placePost, default_lonLat=default_lonLat)
    return render(request, 'admin2/placed_detail.html', context)
