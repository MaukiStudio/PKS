#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.models import Content
from base.legacy.urlnorm import norms as url_norms


class Url(Content):
    # MUST override
    @property
    def contentType(self):
        return 'url'

    @property
    def accessedType(self):
        return 'html'

    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        return url_norms(raw_content.strip())
