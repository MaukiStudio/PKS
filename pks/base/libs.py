#-*- coding: utf-8 -*-
from __future__ import unicode_literals

import numpy as np
from django.contrib.gis.geos import GEOSGeometry

from base.utils import call


def distance_geography(p1, p2):
    from geopy.distance import vincenty as vincenty_distance
    from geopy import Point
    geopy_p1 = Point(p1.y, p1.x)
    geopy_p2 = Point(p2.y, p2.x)
    return vincenty_distance(geopy_p1, geopy_p2).meters


# TODO : 느낌만으로 만든 휴리스틱. 개선 필요
# 특히 distance 함수에 버그가 있던 시절에 실험을 통한 느낌으로 만든 것이라 더더욱...
def distance_geography_group(g1, g2):
    d1 = distance_geography(g1.lonLat, g2.lonLat)
    g1.distance = distance_geography
    g2.distance = distance_geography
    d2 = max(d1 - g1.radius - g2.radius, 0)
    return (d1+d2)/2.0


class Group(object):
    def __init__(self, members=None):
        self.leader = None
        if not members:
            members = list()
        self.members = members
        self.type = None
        self.distance = None

        self._cache_flat_members = None
        self._cache_lonLat_median = None
        self._cache_lonLat_min_max = None
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
                    self._cache_flat_members = [member for member in self.members]
            else:
                self._cache_flat_members = []
        return self._cache_flat_members

    @property
    def lonLat(self):
        return self.lonLat_median

    @property
    def lonLat_median(self):
        if not self._cache_lonLat_median:
            arr_lon = np.array([e.lonLat.x for e in self.members])
            arr_lat = np.array([e.lonLat.y for e in self.members])
            lon = np.median(arr_lon)
            lat = np.median(arr_lat)
            self._cache_lonLat_median = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
        return self._cache_lonLat_median

    @property
    def lonLat_min_max(self):
        if not self._cache_lonLat_min_max:
            arr_lon = np.array([e.lonLat.x for e in self.members])
            arr_lat = np.array([e.lonLat.y for e in self.members])
            # TODO : 근사임. 문제가 있다면 정확한 구현으로 변경
            lon = (arr_lon.min() + arr_lon.max())/2.0
            lat = (arr_lat.min() + arr_lat.max())/2.0
            self._cache_lonLat_min_max = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
        return self._cache_lonLat_min_max

    @property
    def radius(self):
        if not self._cache_radius:
            lonLat = self.lonLat
            arr_distance = np.array([self.distance(lonLat, member.lonLat) for member in self.members])
            '''
            arr_distance_positive = arr_distance[arr_distance > 0]
            m = 0
            if len(arr_distance_positive) > 0:
                m = np.median(arr_distance_positive)
            if len(arr_distance[arr_distance < m]) > 0:
                arr_distance[arr_distance < m][0] = m
            self._cache_radius = np.median(arr_distance[arr_distance >= m])
            #'''
            self._cache_radius = arr_distance.max()
        return self._cache_radius

    @property
    def radius_min_max(self):
        lonLat = self.lonLat_min_max
        arr_distance = np.array([self.distance(lonLat, member.lonLat) for member in self.members])
        return arr_distance.max()

    @property
    def first(self):
        return self.members[0]

    @property
    def last(self):
        return self.members[-1]

    @property
    def count(self):
        return len([member for member in self.flat_members if member.timestamp])


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
        #self.dump_dmat()
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
