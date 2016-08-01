#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import F

from place.models import UserPlace
from base.libs import Group, Clustering
from importer.tasks import distance_geography


class RegionClustering(Clustering):
    def step_04_remove_intersection(self):
        for i in xrange(self.size):
            gcs = [(n, (self.dmat[:, n] < self.threshold).sum()) for n in xrange(self.size)]
            gcs.sort(key=lambda g: g[1], reverse=True)
            gi = self.dmat[:, gcs[i][0]]
            for j in xrange(i+1, self.size):
                gj = self.dmat[:, gcs[j][0]]
                gj[gi < self.threshold] = self.threshold

        #'''
        for i in xrange(self.size):
            ri = self.dmat[i, :]
            i_group_cnt = (ri < self.threshold).sum()
            if i_group_cnt != 1:
                raise NotImplementedError
        #'''

        return True


def get_proper_uplaces_qs(vd, qs=None):
    if not qs:
        qs = UserPlace.objects.all()
    qs = qs.filter(vd_id__in=vd.realOwner_vd_ids)
    qs = qs.exclude(id__in=vd.realOwner_duplicated_uplace_ids)
    qs = qs.filter(mask=F('mask').bitand(~1))   # is_drop == True 인것 제외
    qs = qs.filter(mask=F('mask').bitand(~16))  # is_empty == True 인것 제외
    return qs


def compute_regions(uplaces=None, vd=None):
    if not uplaces:
        if not vd:
            raise NotImplementedError
        uplaces = list(get_proper_uplaces_qs(vd).exclude(lonLat=None))
        for uplace in uplaces:
            uplace.value = uplace.lonLat
            uplace.timestamp = uplace.modified
    if len(uplaces) == 0:
        return None

    group0 = Group()
    group0.members = uplaces
    m_value = group0.lonLat
    from place.models import RADIUS_LOCAL_RANGE
    cluster = RegionClustering(group0, RADIUS_LOCAL_RANGE, distance_geography, m_value, True)
    cluster.run()
    elements = cluster.result
    for e in elements:
        e.type = 'lonLat'

    for i in [6, 5, 4]:
        group0 = Group()
        group0.members = elements
        m_value = group0.lonLat
        cluster = RegionClustering(group0, i*1000, distance_geography, m_value, True)
        cluster.run()
        cluster.result.sort(key=lambda g: g.count, reverse=True)
        for r in cluster.result:
            uplace = UserPlace(lonLat=r.lonLat)
            uplace.value = uplace.lonLat
            uplace.timestamp = 0
            g = Group([uplace])
            g.type = 'lonLat'
            elements.append(g)

    result = [member for member in cluster.result if member.count > 0]
    result.sort(key=lambda g: g.count, reverse=True)
    for g in result:
        g.distance = distance_geography
    return result
