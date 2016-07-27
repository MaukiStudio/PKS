# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'k-#u@ot7=juqps99cjy5wz78e0ljq0og#pv2a5&u2f@+4#n+i6'
USER_ENC_KEY = 'wEy-jbl4InBNmJh6hriCBsKomeQsS5wKe66dJPAHr-o='
VD_ENC_KEY = 'TTlrdjLDsgcN63Pjd9dU8CvZ4bllcL8nkJejTAR2EAY='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Server's Url Host
SERVER_HOST = 'http://neapk-test01.japaneast.cloudapp.azure.com'

# Work Environment or Not
# If true, Unit Tests will remove all media files
WORK_ENVIRONMENT = False

# REDIS SERVER
REDIS_SERVER_IP = '127.0.0.1'

# DISABLE no-free API
DISABLE_NO_FREE_API = True
