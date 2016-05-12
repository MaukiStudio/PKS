#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

# DO NOT DELETE
from pks.celery import app

from celery import Task
from base.utils import get_timestamp


class ImporterTask(Task):

    def run(self, imp):
        imp = imp.reload()
        ts = get_timestamp()
        if imp.started and not imp.ended:
            # TODO : 시간 체크가 아니라 실제 celery task 가 실행되고 있는지를 확인하는 구현으로 변경
            if ts - imp.started < 12*60*60*1000:
                return False

        result = True
        imp.started = ts
        imp.ended = None
        imp.save()

        # 현재는 ImporterTask 가 하는 일은 없다
        # TODO : 향후 iplace 를 물리적 혹은 User vds 들을 합친 VD 등을 생성하는 튜닝 진행 시 추가 구현 필요

        # ProxyTask 처리
        try:
            r = imp.publisher.start()
            if r.failed():
                print('ImporterTask : if r.failed()')
                result = False
        except:
            print('ImporterTask : except')
            result = False

        imp.ended = get_timestamp()
        imp.save()
        return result


class ProxyTask(Task):

    def run(self, proxy):
        proxy = proxy.reload()
        ts = get_timestamp()
        if proxy.started and not proxy.ended:
            # TODO : 시간 체크가 아니라 실제 celery task 가 실행되고 있는지를 확인하는 구현으로 변경
            if ts - proxy.started < 12*60*60*1000:
                return False

        result = True
        proxy.started = ts
        proxy.ended = None
        proxy.save()

        # guide 에 따른 분기 처리
        guide_type = proxy.guide['type']
        if guide_type == 'nothing':
            pass
        elif guide_type == 'images':
            # TODO : 향후엔 별도로 생성한 VD 에 해당 유저의 uplace 정보를 모으는 형태의 튜닝 필요
            result = True
        elif guide_type == 'user':
            task = ImagesProxyTask()
            result = task.run(proxy)
        else:
            print('ProxyTask : else')
            result = False

        proxy.ended = get_timestamp()
        proxy.save()
        return result


class ImagesProxyTask(Task):

    def run(self, proxy):
        return True


