#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import numpy as np

from base.utils import get_timestamp
from image.models import RawFile, Image

GROUPING_DISTANCE_THRESHOLD = 1000


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
        self.imgs = None
        self.size = None
        self.origin = None
        self.dmat = None
        self.results = None

    def run(self, proxy):
        from base.utils import get_timestamp
        self.proxy = proxy
        self.source = self.proxy.vd.parent

        #self.call(self.step_01_task_rfs)
        #self.call(self.step_02_task_images)
        self.call(self.step_03_prepare_images)
        self.call(self.step_04_prepare_variables)
        self.call(self.step_05_prepare_distance_matrix)
        self.call(self.step_06_merge_groups)
        self.call(self.step_07_remove_intersection)

        self.call(self.step_99_generate_report)

        print('complete')
        return True

    def call(self, func):
        from base.utils import get_timestamp
        ts_start = get_timestamp()
        if not func():
            raise NotImplementedError
        ts_end = get_timestamp()
        func_name = str(func).split(' ')[2]
        print('%s(): %0.1f' % (func_name, (ts_end - ts_start)/1000.0))

    def distance(self, p1, p2):
        from geopy.distance import vincenty as vincenty_distance
        return int(round(vincenty_distance(p1, p2).meters))

    def dump_imgs(self):
        print('')
        for img in self.imgs:
            print('%d: %s: (%0.4f, %0.4f)' % (img.dist_from_origin, img.uuid, img.lonLat.x, img.lonLat.y))

    def dump_dmat(self):
        print('')
        print(self.dmat)

        group_cnt = 0
        for i in xrange(self.size):
            ci = self.dmat[:, i]
            if (ci < GROUPING_DISTANCE_THRESHOLD).any():
                group_cnt += 1
        print('group_cnt=%d' % group_cnt)

        missing_cnt = 0
        intersection_cnt = 0
        for j in xrange(self.size):
            cj = self.dmat[j, :] < GROUPING_DISTANCE_THRESHOLD
            if (~cj).all():
                missing_cnt += 1
            if cj.sum() > 1:
                intersection_cnt += 1
        print('missing_cnt=%d, intersection_cnt=%d' % (missing_cnt, intersection_cnt))

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
            if img.task(vd=self.source):
                #print(img)
                pass
        print('step_02_task_images()')
        print('len(rfs1):%d, len(imgs):%d' % (len(rfs1), len(imgs)))

        '''
        similars = Image.objects.filter(rf__in=rfs1).exclude(similar=None).order_by('content')
        print('similars: %d' % len(similars))
        for img in similars:
            print('(%02d, %02d) : %s == %s' % (Image.hamming_distance(img.phash, img.similar.phash),
                                               Image.hamming_distance(img.dhash, img.similar.dhash),
                                               img.content, img.similar.content))
        '''

        return True

    def step_03_prepare_images(self):
        rfs1 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        sames = RawFile.objects.filter(vd=self.source.id).exclude(same=None)
        rfs2 = RawFile.objects.filter(id__in=sames).exclude(vd=self.source.id)
        self.imgs = list(Image.objects.filter(rf__in=rfs1 | rfs2).exclude(lonLat=None).exclude(timestamp=None))
        self.size = len(self.imgs)
        print('step_03_take_images()')
        print('len(rfs1):%d, len(sames):%d, len(rfs2):%d, len(self.imgs):%d' %
              (len(rfs1), len(sames), len(rfs2), self.size))
        return True

    def step_04_prepare_variables(self):
        from django.contrib.gis.geos import GEOSGeometry
        arr_lon = np.array([img.lonLat.x for img in self.imgs])
        arr_lat = np.array([img.lonLat.y for img in self.imgs])
        self.origin = GEOSGeometry('POINT(%f %f)' % (np.median(arr_lon), np.median(arr_lat)), srid=4326)
        print(self.origin)
        for img in self.imgs:
            img.dist_from_origin = self.distance(self.origin, img.lonLat)
        self.imgs.sort(lambda a, b: a.dist_from_origin - b.dist_from_origin)
        #self.dump_imgs()
        return True

    def step_05_prepare_distance_matrix(self):
        self.dmat = np.zeros((self.size, self.size), dtype=int)
        print(self.dmat.shape)
        cnt = 0
        for i in xrange(self.size):
            for j in xrange(i+1, self.size):
                a = self.imgs[i].dist_from_origin
                b = self.imgs[j].dist_from_origin
                min = abs(a - b)
                if min < GROUPING_DISTANCE_THRESHOLD:
                    self.dmat[i, j] = self.distance(self.imgs[i].lonLat, self.imgs[j].lonLat)
                    cnt += 1
                else:
                    self.dmat[i, j] = min
        for i in xrange(self.size):
            for j in xrange(i):
                self.dmat[i, j] = self.dmat[j, i]
        print(cnt)
        self.dump_dmat()
        return True

    def step_06_merge_groups(self):
        merged_into = 0
        merged_back = 0
        for i in xrange(self.size):
            for j in xrange(i+1, self.size):
                ci = self.dmat[:, i] < GROUPING_DISTANCE_THRESHOLD
                cj = self.dmat[:, j] < GROUPING_DISTANCE_THRESHOLD

                if ((~ci) | cj).all():
                    merged_into += 1
                    self.dmat[:, i] = GROUPING_DISTANCE_THRESHOLD
                    break
                if ((~cj) | ci).all():
                    merged_back += 1
                    self.dmat[:, j] = GROUPING_DISTANCE_THRESHOLD
                    continue
        print('merged_into=%d, merged_back=%d' % (merged_into, merged_back))
        self.dump_dmat()
        return True

    def step_07_remove_intersection(self):
        for i in xrange(self.size):
            ri = self.dmat[i, :]
            i_group_cnt = (ri < GROUPING_DISTANCE_THRESHOLD).sum()
            if i_group_cnt <= 0:
                raise NotImplementedError
            if i_group_cnt == 1:
                continue

            # intersection 제거
            min = ri.min()
            argmin= ri.argmin()
            ri[:] = GROUPING_DISTANCE_THRESHOLD
            ri[argmin] = min
        self.dump_dmat()
        return True

    def step_99_generate_report(self):
        self.results = list()
        for i in xrange(self.size):
            ci = self.dmat[:, i]
            if (ci < GROUPING_DISTANCE_THRESHOLD).any():
                group = dict()
                self.results.append(group)
                group['leader'] = self.imgs[i]
                group['members'] = list()
                for j in xrange(self.size):
                    if ci[j] < GROUPING_DISTANCE_THRESHOLD:
                        group['members'].append(self.imgs[j])
                group['members'].sort(lambda a, b: int(a.timestamp - b.timestamp))
        return True
