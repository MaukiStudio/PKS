echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" > temp.list
sudo cp temp.list /etc/apt/sources.list.d/pgdg.list
rm temp.list
sudo wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

sudo apt-get install -y python-pip python-dev liblapack3
sudo apt-get install -y libpq-dev postgresql-9.5 postgresql-contrib-9.5 postgresql-client-9.5
sudo apt-get install -y postgresql-9.5-postgis-2.2
sudo apt-get install -y python-psycopg2

sudo easy_install -U pip
hash -r

sudo pip install -r requirements.txt --upgrade
sudo -u postgres psql -a -f initdb.sql

cd ../pks
./notify_model_changed.sh

