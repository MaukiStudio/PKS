sudo apt update -y
sudo apt upgrade -y
sudo reboot

sudo apt install -y openssh-server
sudo apt install -y git vim screen
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y postgis postgresql-9.5-postgis-2.2
sudo apt install -y rabbitmq-server
sudo apt install -y redis-server

sudo apt install -y python-dev
sudo apt install -y python-pip
sudo -H pip install --upgrade pip
sudo apt install -y python-psycopg2 python-lxml
sudo apt install -y libpq-dev libxml2-dev libxslt1-dev libopenblas-dev
sudo -H pip install -r requirements.txt --upgrade

sudo -u postgres psql -a -f initdb.sql
echo "export DJANGO_SETTINGS_MODULE=pks.settings" >> ~/.bashrc
source ~/.bashrc

cd ../pks
cp pks/settings_deploy_sample.py pks/settings_deploy.py
vi pks/settings_deploy.py
screen celery -A pks worker -l info
python manage.py makemigrations
sudo -u postgres psql -a -f .script/superuser.sql
python manage.py migrate
screen python manage.py runserver 0.0.0.0:8000
py.test --create-db
sudo -u postgres psql -a -f .script/nosuperuser.sql
python manage.py createsuperuser
