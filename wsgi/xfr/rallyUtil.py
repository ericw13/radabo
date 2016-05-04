import os

def get_api_key():
    if 'RALLY_API_KEY' in os.environ:
        api_key = os.environ['RALLY_API_KEY']
    else:
        api_key = open(os.path.expanduser('~/.rally')).read().strip()

    return api_key
