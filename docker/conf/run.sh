#!/bin/sh

# Sets up DB
python /opt/radabo/app/manage.py makemigrations && python /opt/radabo/app/manage.py migrate

echo "Finished migrations"
set -e

# Apache gets grumpy about PID files pre-existing
rm -f /usr/local/apache2/logs/httpd.pid

exec httpd -DFOREGROUND
