sudo -u postgres psql -a -f .script/nosuperuser.sql
python manage.py makemigrations --noinput
sudo -u postgres psql -a -f .script/superuser.sql
python manage.py migrate --noinput
py.test --create-db
sudo -u postgres psql -a -f .script/nosuperuser.sql

