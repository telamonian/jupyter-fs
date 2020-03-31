#!/usr/bin/env python
# *****************************************************************************
#
# Copyright (c) 2019, the jupyter-fs authors.
#
# This file is part of the jupyter-fs library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.

import atexit
import docker
import os
import shutil
import signal
from smb.SMBConnection import SMBConnection
import sys
import time

__all__ = ['smb_user', 'smb_passwd', 'startServer', 'RootDirUtil']

smb_user = 'smb_local'
smb_passwd = 'smb_local'

_dir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))

def startServer(host=None, name_port=137):
    ports = dict((
        ('137/udp', name_port),
        ('138/udp', 138),
        ('139/tcp', 139),
        ('445/tcp', 445),
    ))

    if host is not None:
        for key,val in ports.items():
            ports[key] = (host, val)

    # init docker
    docker_client = docker.from_env(version='auto')
    docker_client.info()

    # set up smb.conf
    shutil.copy(os.path.join(_dir, 'smb.conf.template'), os.path.join(_dir, 'smb.conf'))

    # run the docker container
    smb_container = docker_client.containers.run(
        'dperson/samba', 'samba.sh -n -p -u "{user};{passwd}"'.format(user=smb_user, passwd=smb_passwd),
        detach=True,
        ports=ports,
        remove=True,
        tmpfs={'/shared': 'size=3G,uid=1000'},
        tty=True,
        volumes={
            os.path.join(_dir, "smb.conf"): {"bind": "/etc/samba/smb.conf", "mode": "rw"}
        },
        # network_mode='host',
    )

    atexit.register(smb_container.kill)
    # atexit.register(smb_container.remove)

    # wait for samba to start up
    timeout = 0
    while True:
        if b"daemon 'smbd' finished starting up" in smb_container.logs():
            break

        if timeout >= 100:
            raise RuntimeError('docker dperson/samba timed out while starting up')

        timeout += 1
        time.sleep(1)

    return smb_container


class RootDirUtil:
    def __init__(
        self,
        dir_name,
        endpoint_url,
        my_name='local',
        remote_name='sambatest'
    ):
        self.dir_name = dir_name
        self.endpoint_url = endpoint_url
        self.my_name = my_name
        self.remote_name = remote_name

    def exists(self):
        conn = self.resource()

        return self.dir_name in conn.listShares()

    def create(self):
        """taken care of by smb.conf
        """
        pass

    def _delete(self, path, conn):
        for p in conn.listPath(self.dir_name, path):
            if p.filename!='.' and p.filename!='..':
                subpath = os.path.join(path, p.filename)

                if p.isDirectory:
                    self._delete(subpath, conn)
                    conn.deleteDirectory(self.dir_name, subpath)
                else:
                    conn.deleteFiles(self.dir_name, subpath)

    def delete(self):
        conn = self.resource()

        self._delete('', conn)

    def resource(self):
        kwargs = dict(
            username=smb_user,
            password=smb_passwd,
            my_name=self.my_name,
            remote_name=self.remote_name
        )

        conn = SMBConnection(**kwargs)
        assert conn.connect(self.endpoint_url, 139)

        return conn


if __name__ == "__main__":
    def sigHandler(signo, frame):
        sys.exit(0)

    # make sure the atexit-based docker cleanup runs on ctrl-c
    signal.signal(signal.SIGINT, sigHandler)
    # signal.signal(signal.SIGTERM, sigHandler)

    container = startServer(name_port=3669)

    old_log = ''
    while True:
        new_log = container.logs()
        if old_log != new_log:
            print(new_log)
            old_log = new_log

        time.sleep(1)