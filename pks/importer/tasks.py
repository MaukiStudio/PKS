#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import numpy as np
from django.contrib.gis.geos import GEOSGeometry

from base.utils import get_timestamp
from image.models import RawFile, Image, IMG_PD_HDIST_THREASHOLD

CLUSTERING_MAX_DISTANCE_THRESHOLD = 1300    # meters
CLUSTERING_TIMEDELTA_THRESHOLD = 10+1       # minutes
CLUSTERING_MIN_DISTANCE_THRESHOLD = 4+1+1+1 # meters


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
    #print('%s(): %0.1f' % (func_name, (ts_end - ts_start)/1000.0))


class Group(object):
    def __init__(self):
        self.leader = None
        self.members = list()
        self.type = None
        self.distance = None

        self._cache_flat_members = None
        self._cache_lonLat = None
        self._cache_radius = None

    @property
    def value(self):
        if self.type == 'lonLat':
            return self.lonLat
        return self

    @property
    def timestamp(self):
        return min([member.timestamp for member in self.members])

    @property
    def flat_members(self):
        if not self._cache_flat_members:
            if self.members and self.members[0]:
                if type(self.members[0]) == Group:
                    self._cache_flat_members = sum([member.flat_members for member in self.members], [])
                else:
                    self._cache_flat_members = [img for img in self.members]
            else:
                self._cache_flat_members = []
        return self._cache_flat_members

    @property
    def lonLat(self):
        if not self._cache_lonLat:
            arr_lon = np.array([e.lonLat.x for e in self.flat_members])
            arr_lat = np.array([e.lonLat.y for e in self.flat_members])
            lon = np.median(arr_lon)
            lat = np.median(arr_lat)
            #lon = (arr_lon.min() + arr_lon.max())/2
            #lat = (arr_lat.min() + arr_lat.max())/2
            self._cache_lonLat = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
        return self._cache_lonLat

    @property
    def radius(self):
        if not self._cache_radius:
            lonLat = self.lonLat
            arr_distance = np.array([self.distance(lonLat, member.lonLat) for member in self.flat_members])
            #self._cache_radius = np.median(arr_distance)
            self._cache_radius = arr_distance.max()
            if self._cache_radius > CLUSTERING_MIN_DISTANCE_THRESHOLD:
                self._cache_radius = CLUSTERING_MIN_DISTANCE_THRESHOLD
        return self._cache_radius

    @property
    def first(self):
        return self.members[0]

    @property
    def last(self):
        return self.members[-1]


def distance_geography(p1, p2):
    from geopy.distance import vincenty as vincenty_distance
    return vincenty_distance(p1, p2).meters


def distance_geography_group(g1, g2):
    #distances = np.array([distance_geography(e1.lonLat, e2.lonLat) for e1 in g1.members for e2 in g2.members])
    #return distances.min()
    g1.distance = distance_geography
    g2.distance = distance_geography
    return max(distance_geography(g1.lonLat, g2.lonLat) - g1.radius - g2.radius, 0)


class ImagesProxyTask(object):

    def __init__(self):
        self.proxy = None
        self.source = None
        self.imgs = None
        self.size = None
        self.result = list()
        self.result2 = list()

    def run(self, proxy):
        self.proxy = proxy
        self.source = self.proxy.vd.parent

        call(self.step_01_task_rfs)
        # TODO : 한번만 돌려도 동일한 결과가 나오는 알고리즘으로 변경
        for i in range(3):
            call(self.step_02_task_images)
        self.dump_similars()
        call(self.step_03_prepare_images)
        call(self.step_04_first_clustering_by_geography_distance)
        call(self.step_05_second_clustering_by_timedelta_distance)
        call(self.step_06_third_clustering_by_hamming_distance)
        call(self.step_07_fourth_clustering_by_geography_distance)

        print('')
        print('complete!!!')
        return True

    def dump_similars(self):
        rfs1 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        similars = Image.objects.filter(rf__in=rfs1).exclude(similar=None).order_by('content')
        print('similars: %d' % len(similars))
        for img in similars:
            d_p = Image.hamming_distance(img.phash, img.similar.phash)
            d_d = Image.hamming_distance(img.dhash, img.similar.dhash)
            dist = img.pd_hamming_distance(img.similar)
            if dist == IMG_PD_HDIST_THREASHOLD-1:
                print('(%02d, %02d, %02d) : %s == %s' % (dist, d_p, d_d, img.content, img.similar.content))


    def step_01_task_rfs(self):
        rfs = RawFile.objects.filter(vd=self.source.id).filter(mhash=None)
        for rf in rfs:
            if rf.task():
                #print(rf.file)
                pass
        print('step_01_task_rfs() - len(rfs):%d' % (len(rfs),))
        return True

    def step_02_task_images(self):
        rfs2 = RawFile.objects.filter(vd=self.source.id).filter(same=None).exclude(mhash=None)
        imgs = Image.objects.filter(rf__in=rfs2).filter(lonLat=None)
        for img in imgs:
            if img.task(vd=self.source):
                #print(img)
                pass
        print('step_02_task_images() - len(rfs2):%d, len(imgs):%d' % (len(rfs2), len(imgs)))
        return True

    def step_03_prepare_images(self):
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

    def step_04_first_clustering_by_geography_distance(self):
        group0 = Group()
        group0.members = self.imgs
        m_value = group0.lonLat
        print(m_value)
        cluster = Clustering(group0, CLUSTERING_MAX_DISTANCE_THRESHOLD, distance_geography, m_value, True)
        cluster.run()
        self.result = cluster.result
        print('group_cnt == %d' % len(cluster.result))
        return True

    def step_05_second_clustering_by_timedelta_distance(self):
        def distance_timdelta(p1, p2):
            return abs(int(p1 - p2)/(1000*60))

        group_cnt = 0
        for group1 in self.result:
            arr_ts = np.array([img2.timestamp for img2 in group1.members])
            m_value = arr_ts.min()
            for img2 in group1.members:
                img2.value = img2.timestamp
            cluster = Clustering(group1, CLUSTERING_TIMEDELTA_THRESHOLD, distance_timdelta, m_value, False)
            cluster.run()
            group1.members = cluster.result
            group_cnt += len(cluster.result)
        print('group_cnt == %d' % group_cnt)
        return True

    def step_06_third_clustering_by_hamming_distance(self):
        from uuid import UUID
        def distance_hamming_group(g1, g2):
            distances = [img1.pd_hamming_distance(img2) for img1 in g1.members for img2 in g2.members]
            return min(distances)

        group_cnt = 0
        for group1 in self.result:
            img = Image()
            img.phash = UUID(b'0'*32)
            img.dhash = 0
            m_value = Group()
            m_value.members = [img]
            cluster = Clustering(group1, IMG_PD_HDIST_THREASHOLD, distance_hamming_group, m_value, False)
            cluster.run()
            group1.members = cluster.result
            group_cnt += len(cluster.result)
        print('group_cnt == %d' % group_cnt)
        return True

    def step_07_fourth_clustering_by_geography_distance(self):
        for threshold in xrange(1, CLUSTERING_MIN_DISTANCE_THRESHOLD+1):
            prev_group_cnt = 0
            for iteration in xrange(10):
                group_cnt = 0

                for group1 in self.result:
                    img = Image()
                    img.lonLat = group1.lonLat
                    m_value = Group()
                    m_value.members = [Group()]
                    m_value.members[0].members = [img]
                    cluster = Clustering(group1, threshold, distance_geography_group, m_value, False)
                    cluster.run()
                    group1_members = list()
                    for group2 in cluster.result:
                        merged2 = Group()
                        merged2.members = list()
                        for group3 in group2.members:
                            for group4 in group3.members:
                                merged2.members.append(group4)
                        group1_members.append(merged2)
                    group1.members = group1_members
                    group_cnt += len(group1_members)

                print('group_cnt == %d' % group_cnt)
                if prev_group_cnt == group_cnt:
                    print('inc threshold')
                    break
                else:
                    prev_group_cnt = group_cnt
        return True


class Clustering(object):
    def __init__(self, group, threshold, distance, m_value, verbose=False):
        self.group = group
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
        for e in self.group.members:
            print('%d: %s: %s' % (e.dist_from_m, e, e.value))
        print('')

    def dump_dmat(self):
        if not self.verbose:
            return
        print('')
        print(self.size)
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
        print('')


    def step_01_prepare_variables(self):
        self.size = len(self.group.members)
        for e in self.group.members:
            e.dist_from_m = self.distance(self.m_value, e.value)
        self.group.members.sort(lambda a, b: int(a.dist_from_m - b.dist_from_m))
        #self.dump_elements()
        return True

    def step_02_prepare_distance_matrix(self):
        self.dmat = np.zeros((self.size, self.size), dtype=float)
        cnt = 0
        for i in xrange(self.size):
            for j in xrange(i+1, self.size):
                a = self.group.members[i].dist_from_m
                b = self.group.members[j].dist_from_m
                min = abs(a - b)
                if min < self.threshold:
                    self.dmat[i, j] = self.distance(self.group.members[i].value, self.group.members[j].value)
                    cnt += 1
                else:
                    self.dmat[i, j] = min
        for i in xrange(self.size):
            for j in xrange(i):
                self.dmat[i, j] = self.dmat[j, i]
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
        #print('merged_into=%d, merged_back=%d' % (merged_into, merged_back))
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
        return True

    def step_99_generate_result(self):
        self.dump_dmat()
        self.result = list()
        for i in xrange(self.size):
            ci = self.dmat[:, i]
            if (ci < self.threshold).any():
                group = Group()
                self.result.append(group)
                group.leader = self.group.members[i]
                for j in xrange(self.size):
                    if ci[j] < self.threshold:
                        group.members.append(self.group.members[j])
                group.members.sort(lambda a, b: int(a.timestamp - b.timestamp))

                '''
                if self.verbose and len(group.members) > 1:
                    print('<br/>')
                    print('------------------<br/>')
                    for subgroup in group.members:
                        for member in subgroup.members:
                            print('<img src="%s"/> ' % member.url_summarized)
                    print('<br/>------------------')
                    print('<br/>')
                '''
        return True
