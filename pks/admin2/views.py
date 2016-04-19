#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from place.models import UserPlace
from account.models import VD
from pks.settings import VD_SESSION_KEY


def index(request):
    vd = None
    if VD_SESSION_KEY in request.session:
        vd_id = request.session[VD_SESSION_KEY]
        if vd_id:
            vd = VD.objects.get(id=vd_id)
    context = dict(vd=vd)
    return render(request, 'admin2/index.html', context)


def mapping(request):
    uplaces = UserPlace.objects.filter(place=None)
    context = dict(uplaces=uplaces)
    return render(request, 'admin2/mapping.html', context)
