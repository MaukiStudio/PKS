#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect
from django.db.models import F

from pks.settings import VD_SESSION_KEY
from account.models import VD, RealUser
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
    vd = None
    vd_id = VD_SESSION_KEY in request.session and request.session[VD_SESSION_KEY] or None
    if vd_id:
        vd = VD.objects.get(id=vd_id)
    else:
        user_agent = 'HTTP_USER_AGENT' in request.META and request.META['HTTP_USER_AGENT'][:254] or None
        language = 'HTTP_ACCEPT_LANGUAGE' in request.META and request.META['HTTP_ACCEPT_LANGUAGE'][:2] or None
        vd = VD.objects.create(deviceTypeName='BROWSER', deviceName=user_agent, language=language)
        vd_id = vd.id
        request.session[VD_SESSION_KEY] = vd_id
    if not vd or not vd_id:
        raise NotImplementedError
    return vd


def diaries(request):
    vd = vd_login_for_browser(request)
    from place.libs import get_proper_uplaces_qs
    from base.utils import merge_sort
    uplaces = get_proper_uplaces_qs(vd).exclude(place=None).order_by('-id')
    histories = [VD.objects.get(id=vd_id).accessUplaces for vd_id in vd.realOwner_vd_ids]
    histories_sorted = merge_sort(histories, lambda u: u.accessed)
    return render(request, 'ui/diaries.html', context=dict(uplaces=list(uplaces), history=histories_sorted, vd=vd))


def init(request):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.filter(vd=vd).exclude(mask=F('mask').bitand(~16)).first()
    if not uplace:
        uplace = UserPlace.objects.create(vd=vd, is_empty=True)
    return redirect('../%s/paste/' % uplace.uuid)


def paste(request, uplace_id):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.get(vd_id__in=vd.realOwner_vd_ids, id=uplace_id)

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
                return redirect('/ui/diaries/%s/' % uplace.aid)

    return render(request, 'ui/paste.html', context=dict(uplace=uplace))


def make_shorten_url(request, uplace_id):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.get(vd_id__in=vd.realOwner_vd_ids, id=uplace_id)
    uplace.make_shorten_url()
    return redirect('../paste/')


def detail(request, enc_uplace_id):
    vd = vd_login_for_browser(request)
    uplace_id = UserPlace.aid2id(enc_uplace_id)
    uplace = UserPlace.objects.get(id=uplace_id)
    desc = uplace.userPost.note or uplace.placePost.addr or '사진을 공유하는 새로운 방법!'
    from pks.settings import SERVER_HOST
    url = uplace.wrapping_shorten_url
    if not url:
        url = '%s%s' % (SERVER_HOST, request.get_full_path())
    vd.add_access_history(uplace)
    return render(request, 'ui/detail.html', context=dict(uplace=uplace, url=url, desc=desc))


def register_email(request):
    vd = vd_login_for_browser(request)
    email = None
    if request.method == 'POST':
        email = request.POST['email']
        if email:
            r = vd.send_confirm_email(email)
            if not r:
                raise NotImplementedError
    return render(request, 'ui/register_email.html', context=dict(email=email, ru=vd.realOwner))


def temp(request, uplace_id):
    vd = vd_login_for_browser(request)
    uplace = UserPlace.objects.get(vd_id__in=vd.realOwner_vd_ids, id=uplace_id)

    if request.method == 'POST':
        pb = uplace.userPost.copy()
        pb.images = list()
        pb.notes = list()
        for img_uuid in request.POST.getlist('images'):
            img = Image.get_from_uuid(img_uuid)
            pb.images.append(img)
        for note_uuid in request.POST.getlist('notes'):
            note = PlaceNote.get_from_uuid(note_uuid)
            pb.notes.append(note)
        uplace_temp = UserPlace.objects.create(vd=vd, is_bounded=True, place=uplace.place, lonLat=uplace.lonLat)
        pp = PostPiece.create_smart(uplace_temp, pb)
        return redirect('../../%s/paste/' % uplace_temp.uuid)

    return render(request, 'ui/temp.html', context=dict(uplace=uplace))
