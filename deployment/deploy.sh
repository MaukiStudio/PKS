cp ../pks/pks/settings_deploy_sample.py ../pks/pks/settings_deploy.py
vi ../pks/pks/settings_deploy.py

sudo cp pgdg.list /etc/apt/sources.list.d/pgdg.list
sudo wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update -y
sudo apt-get upgrade -y

sudo apt-get install -y python-pip python-dev liblapack3
sudo apt-get install -y libpq-dev postgresql-9.5 postgresql-contrib-9.5 postgresql-client-9.5
sudo apt-get install -y postgresql-9.5-postgis-2.2
sudo apt-get install -y python-psycopg2
sudo apt-get install -y rabbitmq-server

sudo easy_install -U pip
hash -r

sudo -H pip install -r requirements.txt --upgrade
sudo -u postgres psql -a -f initdb.sql

cd ../pks
./notify_model_changed.sh
