#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from glob import glob
from PIL import Image as PIL_Image
from rest_framework import status
from json import loads as json_loads
from requests import post as requests_post

#from pks.settings import SERVER_HOST
SERVER_HOST = 'http://192.168.1.2:8000'


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
    auth_user_token = 'gAAAAABXN2sAlTeWvJG49cfhCyj_40EkyTc8MPz6325TKx16zqI-BrgZzA9blzDH_C2AnXtuIcw0ditCd-FSvh2eQyQzxMj5pvBocqS5boEbmU9BGePQmoqjqp5kaZBs0kZz_O3QUL7L'
    auth_vd_token = 'gAAAAABXN2tkHugDm828t0Dzk_ajzj2wzjnI9Q3vn_Rw2lkiaqAuungodHChAk80YMZ8y-zMA8S68q7MKZcY2NLiHsua7_ZYSA=='
    auth_token = {'auth_user_token': auth_user_token, 'auth_vd_token': auth_vd_token}
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


#prepare_images()
register_images()
