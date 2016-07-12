from settings import *
CACHES['default']['LOCATION'] = 'redis://%s:6379/2' % REDIS_SERVER_IP
