#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import F

from place.models import UserPlace
from base.libs import Group, Clustering
from importer.tasks import distance_geography
from importer.tasks import CLUSTERING_MAX_DISTANCE_THRESHOLD, CLUSTERING_MIN_DISTANCE_THRESHOLD


def compute_regions(vd):
    uplaces = list(UserPlace.objects.filter(vd__in=vd.realOwner_vd_ids).filter(mask=F('mask').bitand(~1)).exclude(lonLat=None))
    print(len(uplaces))
    for uplace in uplaces:
        uplace.value = uplace.lonLat
        uplace.timestamp = uplace.modified

    group0 = Group()
    group0.members = uplaces
    m_value = group0.lonLat
    cluster = Clustering(group0, CLUSTERING_MIN_DISTANCE_THRESHOLD*2, distance_geography, m_value, True)
    cluster.run()

    '''
    group0 = Group()
    group0.members = cluster.result
    for group1 in group0.members:
        group1.type = 'lonLat'
    m_value = group0.lonLat
    cluster = Clustering(group0, CLUSTERING_MIN_DISTANCE_THRESHOLD, distance_geography, m_value, True)
    cluster.run()
    #'''

    result = cluster.result
    prev_group_cnt = 0
    for i in xrange(10):
        group0.members = result
        m_value = group0.lonLat
        for group1 in group0.members:
            group1.type = 'lonLat'
        cluster = Clustering(group0, CLUSTERING_MAX_DISTANCE_THRESHOLD, distance_geography, m_value, False)
        cluster.run()
        result = [Group(sum([group2.members for group2 in group1.members], [])) for group1 in cluster.result]

        if prev_group_cnt == len(result):
            break
        else:
            prev_group_cnt = len(result)
            print('again...')

    result.sort(lambda a, b: int(a.count - b.count), reverse=True)
    for g in result:
        g.distance = distance_geography

    #'''
    for g in result[:5]:
        print('http://map.naver.com/?dlevel=10&x=%f&y=%f : %d, %0.1f' % (g.lonLat.x, g.lonLat.y, g.count, g.radius))
    #'''
    return result
