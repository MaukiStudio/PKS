#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.db.models import F

from pks.settings import VD_SESSION_KEY
from account.models import VD
from place.models import UserPlace, PostBase, PostPiece, Place
from content.models import PlaceNote, LegacyPlace
from image.models import RawFile, Image


def confirm_ok(request):
    return render(request, 'ui/confirm_ok.html')


def confirm_fail(request):
    return render(request, 'ui/confirm_fail.html')


def vd_login_for_browser(request):
    # 브라우저 로그인은 VD 로그인만 한다
    # API 호출은 User 로그인까지 되어야 가능하도록 해서 권한 관리를 확실히 분리
    # 그리고 브라우저 로그인에서는 token 발급 및 저장은 없도록 해서 보안 관리를 한다
    vd_id = VD_SESSION_KEY in request.session and request.session[VD_SESSION_KEY] or None
    vd = None
    if vd_id:
        try:
            vd = VD.objects.get(id=vd_id)
        except VD.DoesNotExist:
            vd = None
    if not vd:
        user_agent = 'HTTP_USER_AGENT' in request.META and request.META['HTTP_USER_AGENT'][:254] or None
        language = 'HTTP_ACCEPT_LANGUAGE' in request.META and request.META['HTTP_ACCEPT_LANGUAGE'][:2] or None
        vd = VD.objects.create(deviceTypeName='BROWSER', deviceName=user_agent, language=language)
        vd_id = vd.id
        request.session[VD_SESSION_KEY] = vd_id
    return vd


def diaries(request):
    vd = vd_login_for_browser(request)
    return render(request, 'ui/diaries.html')


def init(request):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.filter(vd=vd).exclude(mask=F('mask').bitand(~16)).first()
    if not uplace:
        uplace = UserPlace.objects.create(vd=vd, is_empty=True)
    return redirect('/ui/diaries/%s/paste/' % uplace.uuid)


def paste(request, uplace_id):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.get(vd=vd, id=uplace_id)

    if request.method == 'POST':
        pb = PostBase()
        pb.uuid = uplace.uuid
        if 'note' in request.POST and request.POST['note']:
            note, is_created = PlaceNote.get_or_create_smart(request.POST['note'])
            pb.notes.append(note)
        if request.FILES:
            for file in request.FILES.itervalues():
                rf = RawFile.objects.create(vd=vd, file=file)
                rf.start()
                img, is_created = Image.get_or_create_smart(rf.url)
                pb.images.append(img)
        if 'lp' in request.POST and request.POST['lp']:
            lp, is_created = LegacyPlace.get_or_create_smart(request.POST['lp'])
            pb.lps.append(lp)
            pb_MAMMA = pb.pb_MAMMA
            if pb_MAMMA:
                place, is_created = Place.get_or_create_smart(pb_MAMMA, vd)
                uplace.placed(place)

        if pb.ujson:
            pp = PostPiece.create_smart(uplace, pb)
            if uplace.is_empty:
                uplace.is_empty = False
                uplace.save()
        else:
            if uplace.place:
                return redirect('/ui/diaries/%s/' % uplace.uuid)

    return render(request, 'ui/paste.html', context=dict(userPost=uplace.userPost, placePost=uplace.placePost))


def detail(request, uplace_id):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.get(id=uplace_id)
    return render(request, 'ui/detail.html', context=dict(userPost=uplace.userPost, placePost=uplace.placePost))
