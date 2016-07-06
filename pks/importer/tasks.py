#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import dumps as json_dumps

from base.utils import get_timestamp, call
from image.models import RawFile, Image, IMG_PD_HDIST_THREASHOLD
from place.models import UserPlace, PostPiece, PostBase
from base.libs import Group, Clustering, distance_geography_group, distance_geography

CLUSTERING_MAX_DISTANCE_THRESHOLD = 1500+1      # meters
CLUSTERING_TIMEDELTA_THRESHOLD = 20+1           # minutes
CLUSTERING_MIN_DISTANCE_THRESHOLD = 15+1        # meters


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

    def __init__(self):
        self.proxy = None
        self.source = None
        self.imgs = None
        self.size = None
        self.result = list()

    def run(self, proxy):
        self.proxy = proxy
        self.source = self.proxy.vd.parent

        #'''
        call(self.step_01_task_rfs)
        for i in range(3):     # TODO : 한번만 돌려도 동일한 결과가 나오는 알고리즘으로 변경
            call(self.step_02_task_images)
        #self.dump_similars()
        #'''
        call(self.step_03_prepare_images)
        if self.imgs:
            call(self.step_04_first_clustering_by_geography_distance)
            call(self.step_05_second_clustering_by_timedelta_distance)
            call(self.step_06_third_clustering_by_hamming_distance)
            call(self.step_07_fourth_clustering_by_geography_distance)
            call(self.step_99_generate_uplaces)

        print('')
        print('complete!!!')
        return True

    def dump_similars(self):
        rfs1 = RawFile.objects.filter(vd=self.source).filter(same=None).exclude(mhash=None)
        similars = Image.objects.filter(rf__in=rfs1).exclude(similar=None).order_by('content')
        print('similars: %d' % len(similars))
        for img in similars:
            d_p = Image.hamming_distance(img.phash, img.similar.phash)
            d_d = Image.hamming_distance(img.dhash, img.similar.dhash)
            dist = img.pd_hamming_distance(img.similar)
            if dist == IMG_PD_HDIST_THREASHOLD-1:
                print('(%02d, %02d, %02d) : %s == %s' % (dist, d_p, d_d, img.content, img.similar.content))


    def step_01_task_rfs(self):
        rfs = RawFile.objects.filter(vd=self.source).filter(mhash=None)
        for rf in rfs:
            if rf.task():
                #print(rf.file)
                pass
        print('step_01_task_rfs() - len(rfs):%d' % (len(rfs),))
        return True

    def step_02_task_images(self):
        rfs2 = RawFile.objects.filter(vd=self.source).filter(same=None).exclude(mhash=None)
        imgs = Image.objects.filter(rf__in=rfs2).filter(lonLat=None)
        for img in imgs:
            if img.task(vd=self.source):
                #print(img)
                pass
        print('step_02_task_images() - len(rfs2):%d, len(imgs):%d' % (len(rfs2), len(imgs)))
        return True

    def step_03_prepare_images(self):
        rfs1 = RawFile.objects.filter(vd=self.source).filter(same=None).exclude(mhash=None)
        sames = RawFile.objects.filter(vd=self.source).exclude(same=None)
        rfs2 = RawFile.objects.filter(id__in=sames).exclude(vd=self.source)
        imgs = list(Image.objects.filter(rf__in=rfs1 | rfs2).exclude(lonLat=None).exclude(timestamp=None))
        # TODO : Tuning!!!
        self.imgs = list()
        for img in imgs:
            if PostPiece.objects.filter(vd=self.proxy.vd).filter(data__images__contains=[img.ujson]).first():
                continue
            self.imgs.append(img)
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
        print('step_04:group_cnt == %d' % len(cluster.result))
        return True

    def step_05_second_clustering_by_timedelta_distance(self):
        def distance_timdelta(p1, p2):
            return abs(int(p1 - p2)/(1000*60))

        group_cnt = 0
        for group1 in self.result:
            m_value = min([img2.timestamp for img2 in group1.members])
            for img2 in group1.members:
                img2.value = img2.timestamp
            cluster = Clustering(group1, CLUSTERING_TIMEDELTA_THRESHOLD, distance_timdelta, m_value, False)
            cluster.run()
            group1.members = cluster.result
            group_cnt += len(cluster.result)
        print('step_05:group_cnt == %d' % group_cnt)
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
        print('step_06:group_cnt == %d' % group_cnt)
        return True

    def step_07_fourth_clustering_by_geography_distance(self):
        for threshold in xrange(1, CLUSTERING_MIN_DISTANCE_THRESHOLD+1):
            #print('threshold = %d' % threshold)
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
                    group1.members = [Group(sum([group3.members for group3 in group2.members], [])) for group2 in cluster.result]
                    group_cnt += len(group1.members)

                #print('step_07:group_cnt == %d' % group_cnt)
                if prev_group_cnt == group_cnt:
                    break
                else:
                    prev_group_cnt = group_cnt
        return True

    def step_99_generate_uplaces(self):
        # vd
        vd = self.proxy.vd

        uplace_cnt = 0
        pp_cnt = 0
        for group1 in self.result:
            for group2 in group1.members:
                uplace = UserPlace.objects.create(vd=vd, lonLat=group2.lonLat)
                uplace_cnt += 1
                for group3 in group2.members:
                    pb = PostBase()
                    pb.uplace_uuid = uplace.uuid
                    pb.lonLat = group3.lonLat
                    pb.images = group3.members
                    pp = PostPiece.create_smart(uplace, pb)
                    pp_cnt += 1
        print('uplace_cnt:%d, pp_cnt:%d' % (uplace_cnt, pp_cnt))
        return True
