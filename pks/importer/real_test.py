#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

# Hard Coding
PKS_PATH = '/home/gulby/PKS/pks'
AUTH_USER_TOKEN = 'gAAAAABXN2sAlTeWvJG49cfhCyj_40EkyTc8MPz6325TKx16zqI-BrgZzA9blzDH_C2AnXtuIcw0ditCd-FSvh2eQyQzxMj5pvBocqS5boEbmU9BGePQmoqjqp5kaZBs0kZz_O3QUL7L'
AUTH_VD_TOKEN = 'gAAAAABXN2tkHugDm828t0Dzk_ajzj2wzjnI9Q3vn_Rw2lkiaqAuungodHChAk80YMZ8y-zMA8S68q7MKZcY2NLiHsua7_ZYSA=='
VD_ID = 9
IMP_ID = 3

import sys, os, django
sys.path.append(PKS_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pks.settings')
django.setup()


from glob import glob
from PIL import Image as PIL_Image
from rest_framework import status
from json import loads as json_loads

from pks.settings import SERVER_HOST
from requests import post as requests_post
from importer.models import Importer
from importer.tasks import ImagesProxyTask


def prepare_images():
    for file_name in glob('/media/gulby/HDD/photo/*/*/*'):
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
                pil.save('/media/gulby/HDD/prepared/%s.jpg' % file_name.split('/')[-1].split('.')[0], exif=exif)
            else:
                pil.save('/media/gulby/HDD/prepared/%s.jpg' % file_name.split('/')[-1].split('.')[0])
        except Exception as e:
            print(file_name)
            print(e)


def register_images():
    auth_token = {'auth_user_token': AUTH_USER_TOKEN, 'auth_vd_token': AUTH_VD_TOKEN}
    for file_name in glob('/home/gulby/PKS/temp/prepared/*.jpg'):
        with open(file_name, 'rb') as f:
            files = {'file': f}
            response = requests_post('%s/rfs/' % SERVER_HOST, files=files, data=auth_token)
            if response.status_code != status.HTTP_201_CREATED:
                print(response.text)
                print(file_name)
                print('------------------------------')
                #break
                continue
            img_url = json_loads(response.text)['url']
            data = {'content': img_url}
            response = requests_post('%s/imgs/' % SERVER_HOST, json=data)
            if response.status_code != status.HTTP_201_CREATED:
                print(response.text)
                print(file_name)
                print(img_url)
                print('------------------------------')
                #break
                continue
        #break


def test_images_importer():
    imp = Importer.objects.get(id=IMP_ID)
    task = ImagesProxyTask()
    task.run(imp.publisher)


# by Client
#prepare_images()
#register_images()

# by Server (Celery)
test_images_importer()
