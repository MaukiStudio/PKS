sudo -u postgres psql -a -f .script/nosuperuser.sql
rm account/migrations/0*
rm base/migrations/0*
rm content/migrations/0*
rm functional_tests/migrations/0*
rm image/migrations/0*
rm pks/migrations/0*
rm place/migrations/0*
rm url/migrations/0*
sudo -u postgres psql -a -f .script/superuser.sql
python manage.py reset_db
sudo -u postgres psql -a -f .script/nosuperuser.sql
./notify_model_changed.sh
