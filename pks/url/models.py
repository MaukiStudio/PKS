#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.models import Content


class Url(Content):
    # MUST override
    @property
    def contentType(self):
        return 'url'

    @property
    def accessedType(self):
        return 'html'
