sudo -u postgres psql -a -f .script/nosuperuser.sql
python manage.py makemigrations
sleep 3
sudo -u postgres psql -a -f .script/superuser.sql
python manage.py migrate
sleep 3
py.test --create-db
sudo -u postgres psql -a -f .script/nosuperuser.sql
