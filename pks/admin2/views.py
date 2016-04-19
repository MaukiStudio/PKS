#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from place.models import UserPlace


def index(request):
    uplaces = UserPlace.objects.filter(place=None)
    context = dict(uplaces=uplaces)
    return render(request, 'admin2/index.html', context)


def mapping(request):
    uplaces = UserPlace.objects.filter(place=None)
    context = dict(uplaces=uplaces)
    return render(request, 'admin2/mapping.html', context)
