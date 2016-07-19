#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


def confirm_ok(request):
    return render(request, 'ui/confirm_ok.html')
