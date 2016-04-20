#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect, HttpResponse

from place.models import UserPlace
from account.models import VD
from pks.settings import VD_SESSION_KEY
from place.post import PostBase
from place.models import PostPiece


def index(request):
    user = request.user
    if user.is_authenticated and user.is_active and user.is_staff:
        vd = user.vds.filter(deviceTypeName='ADMIN').order_by('-id')[0]
        request.session[VD_SESSION_KEY] = vd.id
    else:
        redirect('/admin/login/?next=/admin2/')
    return render(request, 'admin2/index.html')


def mapping(request):
    pbs = [uplace.userPost for uplace in UserPlace.objects.filter(place=None)[:100]]
    for pb in pbs:
        for image in pb.images:
            image.summarize()
    context = dict(pbs=pbs)
    return render(request, 'admin2/mapping.html', context)


def mapping_detail(request, uplace_id):
    if request.method == 'POST':
        url = request.POST['url']
        if url in ('삭제', '제거', 'delete','remove'):
            uplace = UserPlace.objects.get(id=uplace_id)
            uplace.delete()
            return redirect('/admin2/mapping/%s.uplace/' % uplace_id)

        # TODO : 완전 리팩토링 필요;;; 일단 임시 땜빵임
        vd = VD.objects.get(id=request.session[VD_SESSION_KEY])

        # PostBase instance 생성
        json_add = '{"urls": [{"content": "%s"}]}' % url
        pb = PostBase(json_add)
        pb.uplace_uuid = '%s.uplace' % uplace_id

        # UserPlace/Place 찾기
        uplace = UserPlace.get_from_post(pb, vd)
        pb.uplace_uuid = uplace.uuid

        # valid check
        if not pb.is_valid(uplace):
            raise ValueError('PostPiece 생성을 위한 최소한의 정보도 없음')

        # PostPiece 생성
        # pp = PostPiece.objects.create(type_mask=0, place=None, uplace=uplace, vd=vd, data=pb.json)

        # 임시적인 어드민 구현을 위해, MAMMA 가 추가로 뽑아준 post 가 있으면 추가로 포스팅
        # TODO : 향후 Django-Celery 구조 도입하여 정리한 후 제거
        pb_MAMMA = pb.pb_MAMMA
        if pb_MAMMA:
            # TODO : Place 생성을 확인하기 위해 get_from_post() 를 호출하는 것은 적절한 구조가 아니다...
            uplace = UserPlace.get_from_post(pb_MAMMA, vd)
            pb_MAMMA.uplace_uuid = uplace.uuid
            pp2 = uplace.place.pps.first()
            if not pp2:
                pp2 = PostPiece.objects.create(type_mask=2, place=uplace.place, uplace=None, vd=vd, data=pb_MAMMA.json)

        # redirect
        return redirect('/admin2/mapping/%s.uplace/' % uplace_id)

    try:
        uplace = UserPlace.objects.get(id=uplace_id)
    except UserPlace.DoesNotExist:
        return HttpResponse('삭제되었습니다')
    userPost = uplace.userPost and uplace.userPost
    placePost = uplace.placePost and uplace.placePost
    context = dict(userPost=userPost, placePost=placePost)
    return render(request, 'admin2/mapping_detail.html', context)
