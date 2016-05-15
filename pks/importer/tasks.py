#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.utils import get_timestamp
from image.models import RawFile, Image

class ImporterTask(object):

    def run(self, imp_id):
        from importer.models import Importer
        imp = Importer.objects.get(id=imp_id)
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


class ProxyTask(object):

    def run(self, proxy_id):
        from importer.models import Proxy
        proxy = Proxy.objects.get(id=proxy_id)
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
        elif guide_type == 'user':
            # TODO : 향후엔 별도로 생성한 VD 에 해당 유저의 uplace 정보를 모으는 형태의 튜닝 필요할지도...
            result = True
        elif guide_type == 'images':
            task = ImagesProxyTask()
            result = task.run(proxy)
        else:
            print('ProxyTask : else')
            result = False

        proxy.ended = get_timestamp()
        proxy.save()
        return result


class ImagesProxyTask(object):

    def __init__(self, *args, **kwargs):
        super(ImagesProxyTask, self).__init__(*args, **kwargs)
        self.proxy = None

    def run(self, proxy):
        self.proxy = proxy
        self.source = self.proxy.vd.parent

        if not self.step01_task_rf():
            return False

        return True

    def step01_task_rf(self):
        rfs = RawFile.objects.filter(vd=self.source.id).filter(mhash=None)
        print(len(rfs))
        for rf in rfs:
            if rf.task_mhash():
                print(rf.file)

        rfs = RawFile.objects.filter(vd=self.source.id).exclude(mhash=None).filter(same=None)
        print(len(rfs))

        print('ImagesProxyTask.step01_task_rf()')
        return True

