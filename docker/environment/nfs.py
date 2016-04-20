# coding=utf-8
"""Author: Tomasz Lichon
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Brings up a nfs server.
"""

from . import docker

def _node_up(image):
    container = docker.run(
        image=image,
        detach=True,
        privileged=True)

    settings = docker.inspect(container)
    ip = settings['NetworkSettings']['IPAddress']

    return {
        'docker_ids': [container],
        'ip': ip,
    }


def up(image):
    return _node_up(image)
