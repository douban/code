# -*- coding: utf-8 -*-

try:
    #from gevent.monkey import patch_all
    #patch_all(subprocess=False, aggressive=False)
    from gevent.monkey import get_original
    from gevent.server import StreamServer
    import select
    select.poll = get_original('select', 'poll')
    import subprocess
    subprocess.Popen = get_original('subprocess', 'Popen')
except ImportError:
    print 'You need install gevent manually! System shutdown.'

from binascii import hexlify
from maria import Maria
from maria.config import config
from vilya.libs.permdir import get_repo_root
from vilya.models.sshkey import SSHKey
from vilya.models.project import CodeDoubanProject as Project
from vilya.models.gist import Gist

config.project_root = get_repo_root()
config.log_file = None
config.host_key_path = './host.key'

app = Maria(config=config)


@app.get_environ
def get_environ_handler(user, path):
    return {'CODE_REMOTE_USER': user}


@app.has_permission
def has_permission_handler(username, path, perm):
    if not username or not path:
        return False

    if path.endswith('.git'):
        path = path[:-4]

    # gist
    if path.startswith('gist/'):
        gist_id = path.rpartition("/")[-1]
        if username == Gist.get(gist_id).owner_id:
            return  True
        return False

    # project
    project = Project.get_by_name(path)
    if not project:
        return False
    if perm == 'read':
        return True
    if not project.can_push:
        return False
    if project.has_push_perm(username):
        return True
    return False


@app.get_user
def get_user_handler(username, key):
    # ssh username
    if username != 'git':
        return None

    # ssh key
    if not key:
        return None
    fingerprint = hexlify(key.get_fingerprint())
    fingerprint = ":".join([fingerprint[i:2+i] for i in range(0, len(fingerprint), 2)])
    sshkey = SSHKey.get_by_fingerprint(fingerprint)
    if not sshkey:
        return 'guest'
    return sshkey.user_id


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='code ssh daemon.')
    parser.add_argument('--host', default='0.0.0.0', type=str)
    parser.add_argument('--port', default=2200, type=int)
    args = parser.parse_args()

    server = StreamServer((args.host, args.port), app)
    server.serve_forever()
