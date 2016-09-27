#-*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import sys, os, django


# Hard Coding
PKS_PATH = '/home/gulby/PKS/pks'

# Hard Coding - for gulby
#'''
AUTH_USER_TOKEN = 'gAAAAABXN2sAlTeWvJG49cfhCyj_40EkyTc8MPz6325TKx16zqI-BrgZzA9blzDH_C2AnXtuIcw0ditCd-FSvh2eQyQzxMj5pvBocqS5boEbmU9BGePQmoqjqp5kaZBs0kZz_O3QUL7L'
AUTH_VD_TOKEN = 'gAAAAABXN2tkHugDm828t0Dzk_ajzj2wzjnI9Q3vn_Rw2lkiaqAuungodHChAk80YMZ8y-zMA8S68q7MKZcY2NLiHsua7_ZYSA=='
VD_ID = 9
IMP_ID = 7
IMAGE_PREPARED_PATH = '/home/gulby/PKS/temp/prepared_gulby'
IMAGE_SOURCE_PATH = '/media/gulby/HDD/photo/gulby/*/*/*'
#'''

# Hard Coding - for newyear
'''
AUTH_USER_TOKEN = 'gAAAAABXPsdbvxTrJ5SFOUZ0Z7Dwm3g4tGV9Z5E5qclzYmbq0SYWacuoTAGg9wAgBkNMUKzFEeR91A4ZNynG6wI_A1A09EKxFIqmUmCjiA4CzJYpSfmP8wgCHoiEOikUaXGYg9dHyMQH'
AUTH_VD_TOKEN = 'gAAAAABXPsea0t-OyghqMSaspTgQ3AU8Zj3MK01VI-KY-MLP3gtHlAIpxx2fR2u5j-3WhWJWBshqCiXpYWENrhJj5Lh9CpES4w=='
VD_ID = 12
IMP_ID = 4
IMAGE_PREPARED_PATH = '/home/gulby/PKS/temp/prepared_newyear'
IMAGE_SOURCE_PATH = '/media/gulby/HDD/photo/newyear/*/*/*'
#'''

# Hard Coding - for usia
'''
AUTH_USER_TOKEN = 'gAAAAABXPzB-wCqwl_SfsfrXdx03k3BkueY-pWyppryWDBCmLkLPE1rJOle6IFek8vqvApzrOZIaY4bhwvDZavUwEadWcPD9qjnGsnAatdCeCSvwtVJ_Bl6gfNHL_xhIfvtMWoXkwjlT'
AUTH_VD_TOKEN = 'gAAAAABXPzGFIZ_vZyYq6O0VpZYKBLfoJuVFJ5H-HWD5lPiN4NswQeDR91uDxgi2wM-MLz2ZVtP9rgirwbcAmiqRaoSRHwD6mA=='
VD_ID = 14
IMP_ID = 5
IMAGE_PREPARED_PATH = '/home/gulby/PKS/temp/prepared_usia'
IMAGE_SOURCE_PATH = '/media/gulby/HDD/photo/usia/*/*'
#'''

# Hard Coding - for jamie
'''
AUTH_USER_TOKEN = 'gAAAAABXPzk71XdglDhVb8-4MpYt3zwVGj9WGVqoawPqp7n93Nqgz7WBJUsxdBHevm3SSNMXZevj6gPJsJNRWDpy65865g7SrdGqCPm4_FAsZkw9B2BfYNAXecZG-pnV-KZ8tAysJcey'
AUTH_VD_TOKEN = 'gAAAAABXPznJ4Zkk-hrKcePD1oi_FFFzD0HKbx8Q_iXyhsnaWVOwvKuBlMWAq576ZtK6D3JU6GZjuPJhp768QgYmgsso6kuWmg=='
VD_ID = 16
IMP_ID = 6
IMAGE_PREPARED_PATH = '/home/gulby/PKS/temp/prepared_jamie'
IMAGE_SOURCE_PATH = '/media/gulby/HDD/photo/jamie/*'
#'''


# Set django env
sys.path.append(PKS_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pks.settings')
django.setup()


def test_compute_regions():
    from place.libs import compute_regions
    from importer.models import Importer
    imp = Importer.objects.get(id=IMP_ID)
    vd = imp.publisher.vd
    result = compute_regions(vd)


test_compute_regions()
