import os

def get_api_key():
    if 'RALLY_API_KEY' in os.environ:
        api_key = os.environ['RALLY_API_KEY']
    elif 'OPENSHIFT_REPO_DIR' in os.environ:
        keypath=os.environ['OPENSHIFT_REPO_DIR'] + 'wsgi/xfr/.rally'
        api_key = open(keypath).read().strip()
    else:
        api_key = open(os.path.expanduser('~/.rally')).read().strip()

    return api_key
