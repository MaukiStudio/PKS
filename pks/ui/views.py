#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from pks.settings import VD_SESSION_KEY
from account.models import VD


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


def ui_list(request):
    vd = vd_login_for_browser(request)
    return render(request, 'ui/list.html')

