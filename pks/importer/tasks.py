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
        self.source = None
        self.imgs = list()

    def run(self, proxy):
        self.proxy = proxy
        self.source = self.proxy.vd.parent

        if not self.step_01_task_rfs():
            return False
        if not self.step_02_task_images():
            return False
        if not self.step_03_take_images():
            return False

        return True

    def step_01_task_rfs(self):
        rfs = RawFile.objects.filter(vd=self.source.id).filter(mhash=None)
        for rf in rfs:
            if rf.task():
                print(rf.file)
        print('step_01_task_rfs()')
        print('len(rfs):%d' % (len(rfs),))
        return True

    def step_02_task_images(self):
        rfs1 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        imgs = Image.objects.filter(rf__in=rfs1).filter(lonLat=None)
        for img in imgs:
            if img.task():
                #print(img.content)
                pass
        print('step_02_task_images()')
        print('len(rfs1):%d, len(imgs):%d' % (len(rfs1), len(imgs)))

        '''
        similars = Image.objects.filter(rf__in=rfs1).exclude(similar=None)
        for img in similars:
            print('%s == %s' % (img.content, img.similar.content))
        '''

        return True

    def step_03_take_images(self):
        rfs1 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        sames = RawFile.objects.filter(vd=self.source.id).exclude(same=None)
        rfs2 = RawFile.objects.filter(id__in=sames).exclude(vd=self.source.id)
        self.imgs = list(Image.objects.filter(rf__in=rfs1 | rfs2).exclude(lonLat=None).exclude(timestamp=None))
        print('step_03_take_images()')
        print('len(rfs1):%d, len(sames):%d, len(rfs2):%d, len(self.imgs):%d' %
              (len(rfs1), len(sames), len(rfs2), len(self.imgs)))
        return True
