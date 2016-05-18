#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import numpy as np
from django.contrib.gis.geos import GEOSGeometry

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


def call(func):
    from base.utils import get_timestamp
    ts_start = get_timestamp()
    if not func():
        raise NotImplementedError
    ts_end = get_timestamp()
    func_name = str(func).split(' ')[2]
    print('%s(): %0.1f' % (func_name, (ts_end - ts_start)/1000.0))


class ImagesProxyTask(object):

    def __init__(self):
        self.proxy = None
        self.source = None
        self.imgs = None
        self.size = None
        self.cluster_01 = None
        self.result = None

    def run(self, proxy):
        self.proxy = proxy
        self.source = self.proxy.vd.parent

        #call(self.step_01_task_rfs_images)
        call(self.step_02_prepare_images)
        call(self.step_03_first_clustering)

        print('')
        print('complete!!!')
        return True

    def dump_similars(self):
        rfs1 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        similars = Image.objects.filter(rf__in=rfs1).exclude(similar=None).order_by('content')
        print('similars: %d' % len(similars))
        for img in similars:
            print('(%02d, %02d) : %s == %s' % (Image.hamming_distance(img.phash, img.similar.phash),
                                               Image.hamming_distance(img.dhash, img.similar.dhash),
                                               img.content, img.similar.content))


    def step_01_task_rfs_images(self):
        rfs = RawFile.objects.filter(vd=self.source.id).filter(mhash=None)
        for rf in rfs:
            if rf.task():
                #print(rf.file)
                pass
        rfs2 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        imgs = Image.objects.filter(rf__in=rfs2).filter(lonLat=None)
        for img in imgs:
            if img.task(vd=self.source):
                #print(img)
                pass
        print('step_01_task_rfs_images() - len(rfs):%d, len(rfs2):%d, len(imgs):%d' % (len(rfs), len(rfs2), len(imgs)))
        #self.dump_similars()
        return True

    def step_02_prepare_images(self):
        rfs1 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        sames = RawFile.objects.filter(vd=self.source.id).exclude(same=None)
        rfs2 = RawFile.objects.filter(id__in=sames).exclude(vd=self.source.id)
        self.imgs = list(Image.objects.filter(rf__in=rfs1 | rfs2).exclude(lonLat=None).exclude(timestamp=None))
        for img in self.imgs:
            img.value = img.lonLat
        self.size = len(self.imgs)
        print('step_03_prepare_images() - len(rfs1):%d, len(sames):%d, len(rfs2):%d, len(self.imgs):%d' %
              (len(rfs1), len(sames), len(rfs2), self.size))
        return True

    def step_03_first_clustering(self):
        arr_lon = np.array([e.lonLat.x for e in self.imgs])
        arr_lat = np.array([e.lonLat.y for e in self.imgs])
        m_value = GEOSGeometry('POINT(%f %f)' % (np.median(arr_lon), np.median(arr_lat)), srid=4326)
        print(m_value)

        def distance_geography(p1, p2):
            from geopy.distance import vincenty as vincenty_distance
            return int(round(vincenty_distance(p1, p2).meters))

        self.cluster_01 = Clustering(self.imgs, 1000, distance_geography, m_value, True)
        self.cluster_01.run()
        self.result = self.cluster_01.result
        return True


class Clustering(object):
    def __init__(self, elements, threshold, distance, m_value, verbose=True):
        self.elements = elements
        self.threshold = threshold
        self.distance = distance
        self.m_value = m_value
        self.verbose = verbose

        self.size = None
        self.dmat = None
        self.result = None

    def run(self):
        call(self.step_01_prepare_variables)
        call(self.step_02_prepare_distance_matrix)
        call(self.step_03_merge_groups)
        call(self.step_04_remove_intersection)
        call(self.step_99_generate_result)

    def dump_elements(self):
        print('')
        for e in self.elements:
            print('%d: %s: %s' % (e.dist_from_median, e, e.value))

    def dump_dmat(self):
        print('')
        print(self.dmat)

        group_cnt = 0
        for i in xrange(self.size):
            ci = self.dmat[:, i]
            if (ci < self.threshold).any():
                group_cnt += 1
        print('group_cnt=%d' % group_cnt)

        missing_cnt = 0
        intersection_cnt = 0
        for j in xrange(self.size):
            cj = self.dmat[j, :] < self.threshold
            if (~cj).all():
                missing_cnt += 1
            if cj.sum() > 1:
                intersection_cnt += 1
        print('missing_cnt=%d, intersection_cnt=%d' % (missing_cnt, intersection_cnt))


    def step_01_prepare_variables(self):
        self.size = len(self.elements)
        for e in self.elements:
            e.dist_from_median = self.distance(self.m_value, e.value)
        self.elements.sort(lambda a, b: a.dist_from_median - b.dist_from_median)
        #self.dump_elements()
        return True

    def step_02_prepare_distance_matrix(self):
        self.dmat = np.zeros((self.size, self.size), dtype=int)
        print(self.dmat.shape)
        cnt = 0
        for i in xrange(self.size):
            for j in xrange(i+1, self.size):
                a = self.elements[i].dist_from_median
                b = self.elements[j].dist_from_median
                min = abs(a - b)
                if min < self.threshold:
                    self.dmat[i, j] = self.distance(self.elements[i].value, self.elements[j].value)
                    cnt += 1
                else:
                    self.dmat[i, j] = min
        for i in xrange(self.size):
            for j in xrange(i):
                self.dmat[i, j] = self.dmat[j, i]
        print(cnt)
        self.dump_dmat()
        return True

    def step_03_merge_groups(self):
        merged_into = 0
        merged_back = 0
        for i in xrange(self.size):
            for j in xrange(i+1, self.size):
                ci = self.dmat[:, i] < self.threshold
                cj = self.dmat[:, j] < self.threshold

                if ((~ci) | cj).all():
                    merged_into += 1
                    self.dmat[:, i] = self.threshold
                    break
                if ((~cj) | ci).all():
                    merged_back += 1
                    self.dmat[:, j] = self.threshold
                    continue
        print('merged_into=%d, merged_back=%d' % (merged_into, merged_back))
        self.dump_dmat()
        return True

    def step_04_remove_intersection(self):
        for i in xrange(self.size):
            ri = self.dmat[i, :]
            i_group_cnt = (ri < self.threshold).sum()
            if i_group_cnt <= 0:
                raise NotImplementedError
            if i_group_cnt == 1:
                continue

            # intersection 제거
            min = ri.min()
            argmin= ri.argmin()
            ri[:] = self.threshold
            ri[argmin] = min
        self.dump_dmat()
        return True

    def step_99_generate_result(self):
        self.result = list()
        for i in xrange(self.size):
            ci = self.dmat[:, i]
            if (ci < self.threshold).any():
                group = dict()
                self.result.append(group)
                group['leader'] = self.elements[i]
                group['members'] = list()
                for j in xrange(self.size):
                    if ci[j] < self.threshold:
                        group['members'].append(self.elements[j])
                group['members'].sort(lambda a, b: int(a.timestamp - b.timestamp))
        return True
