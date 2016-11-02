# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Example Ceph credentials generator.
"""

import os
import rados
import json
import ConfigParser

from luma.credentials import CephCredentials

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

POOL_NAME = config.get('ceph', 'pool_name')
USER = config.get('ceph', 'user')
KEY = config.get('ceph', 'key')
MON_HOST = config.get('ceph', 'mon_host')


def create_user_credentials(storage_type, storage_id, space_name, client_ip,
                            user_details):
    """Creates user credentials for CEPH storage based on provided user data.
    """
    user_id = user_details["id"]
    if user_id == "0":
        return CephCredentials(USER, KEY)

    cluster = rados.Rados(conf=dict())
    cluster.conf_set("key", KEY)
    cluster.conf_set("mon host", MON_HOST)
    cluster.connect()
    user_name = "client.{0}".format(user_id)

    status, response, reason = cluster.mon_command(json.dumps(
        {"prefix": "auth get-or-create", "entity": user_name,
         "caps": ["mon", "allow r", "osd",
                  "allow rw pool={}".format(POOL_NAME)]}), "")
    if status != 0:
        raise RuntimeError(reason)
    user_key = response.split()[-1]

    return CephCredentials(user_name, user_key)
