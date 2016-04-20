#!/bin/bash

python ${OPENSHIFT_REPO_DIR}wsgi/xfr/loadSprint.py
python ${OPENSHIFT_REPO_DIR}wsgi/xfr/loadBacklog.py
