#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import sys, os, django
from glob import glob
from PIL import Image as PIL_Image
from rest_framework import status

from requests import post as requests_post

# Hard Coding
PKS_PATH = '/home/gulby/PKS/pks'
AUTH_USER_TOKEN = 'gAAAAABXN2sAlTeWvJG49cfhCyj_40EkyTc8MPz6325TKx16zqI-BrgZzA9blzDH_C2AnXtuIcw0ditCd-FSvh2eQyQzxMj5pvBocqS5boEbmU9BGePQmoqjqp5kaZBs0kZz_O3QUL7L'
AUTH_VD_TOKEN = 'gAAAAABXN2tkHugDm828t0Dzk_ajzj2wzjnI9Q3vn_Rw2lkiaqAuungodHChAk80YMZ8y-zMA8S68q7MKZcY2NLiHsua7_ZYSA=='
VD_ID = 9
IMP_ID = 3
IMAGE_PREPARED_PATH = '/home/gulby/PKS/temp/prepared'
IMAGE_SOURCE_PATH = '/media/gulby/HDD/photo/gulby/*/*/*'

# Set django env
sys.path.append(PKS_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pks.settings')
django.setup()


def prepare_images():
    os.system('rm -rf %s/*' % (IMAGE_PREPARED_PATH,))
    exif_cnt = 0
    for file_name in glob(IMAGE_SOURCE_PATH):
        try:
            pil = PIL_Image.open(file_name)
            w, h = pil.size
            if w >= h:
                nw = 1280.0
                nh = h * (nw / w)
            else:
                nh = 1280.0
                nw = w * (nh / h)
            nw = int(round(nw))
            nh = int(round(nh))
            pil = pil.resize((nw, nh), PIL_Image.ANTIALIAS)
            exif = 'exif' in pil.info and pil.info['exif'] or None
            if exif:
                pil.save('%s/%s.jpg' % (IMAGE_PREPARED_PATH, file_name.split('/')[-1].split('.')[0]), exif=exif)
                exif_cnt += 1
            else:
                pil.save('%s/%s.jpg' % (IMAGE_PREPARED_PATH, file_name.split('/')[-1].split('.')[0]))
        except Exception as e:
            print(file_name)
            print(e)
    print('exif_cnt : %d' % exif_cnt)


def register_images():
    from pks.settings import SERVER_HOST
    auth_token = {'auth_user_token': AUTH_USER_TOKEN, 'auth_vd_token': AUTH_VD_TOKEN}
    for file_name in glob('%s/*.jpg' % IMAGE_PREPARED_PATH):
        with open(file_name, 'rb') as f:
            files = {'file': f}
            response = requests_post('%s/rfs/' % SERVER_HOST, files=files, data=auth_token)
            if response.status_code != status.HTTP_201_CREATED:
                print(response.text)
                print(file_name)
                print('------------------------------')
                #break
                continue
        #break


def clear_rfs_smart():
    from image.models import RawFile
    rfs = RawFile.objects.filter(mhash=None)
    for rf in rfs:
        rf.task()


def reset_image_task():
    pass
    '''
    from image.models import Image
    imgs = Image.objects.all()
    for img in imgs:
        img.phash = None
        img.dhash = None
        img.similar = None
        img.lonLat = None
        img.timestamp = None
        img.save()
        print(img)
    '''
    '''
    from account.models import VD
    vd = VD.objects.get(id=VD_ID)
    for img in imgs:
        img.task(vd=vd, force_similar=True)
        #print(img)
    '''


def make_report_html(result):
    with open('ImagesImporterReport.html', 'w') as f:
        f.write('<html><body><table border="True">\n')
        for group1 in result:
            for group2 in group1.members:
                f.write('<tr>\n')
                map_url_first = 'http://map.naver.com/?dlevel=13&x=%f&y=%f' % (group2.first.first.lonLat.x, group2.first.first.lonLat.y)
                map_url_last = 'http://map.naver.com/?dlevel=13&x=%f&y=%f' % (group2.last.last.lonLat.x, group2.last.last.lonLat.y)
                f.write('   <td>\n')
                f.write('       <a href="%s" target="_blank"><img src="%s"/></a>' % (map_url_first, group2.first.first.url_summarized))
                f.write('       <a href="%s" target="_blank"><img src="%s"/></a>' % (map_url_last, group2.last.last.url_summarized))
                f.write('   </td>\n')

                f.write('   <td><table border="True"><tr>\n')
                for group3 in group2.members:
                    f.write('       <tr>\n')
                    for member in group3.members:
                        f.write('       <td>')
                        f.write('           <img src="%s"/>' % member.url_summarized)
                        f.write('       </td>')
                    f.write('       </tr>\n')
                f.write('   </tr></table></td>\n')

                f.write('</tr>\n')
        f.write('</table></body></html>\n')
    return True


def test_images_importer():
    from importer.models import Importer
    from importer.tasks import ImagesProxyTask
    imp = Importer.objects.get(id=IMP_ID)
    task = ImagesProxyTask()
    r = task.run(imp.publisher)
    make_report_html(task.result)


# by Client
#prepare_images()
#register_images()


# For Test (Hash...)
#reset_image_task()


# by Server (Celery)
test_images_importer()


# for Test (disk size...)
clear_rfs_smart()
