#! /bin/bash
#docker build -t "radabo" git://git.corp.redhat.com/srv/git/it-bizsys/fin/pj

docker build -t "radabo" /home/ewright/dev/radabo
docker stop radabo && docker rm radabo 
docker run --name "radabo" --net=host -p 127.0.0.1:8000:80 -d \
        -e "DJANGO_DB_NAME=rally" \
        -e "DJANGO_DB_USER=appl" \
        -e "DJANGO_DB_PASSWORD=django" \
        -e "DJANGO_DB_HOST=172.17.0.1" \
        -e "DJANGO_SECRET_DIR=/opt/radabo/app/data/" \
        -e "TERM=xterm-256color" \
        radabo
