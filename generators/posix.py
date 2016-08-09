# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Example posix credentials generator.
"""

import hashlib
import ConfigParser
import os

from luma.credentials import PosixCredentials

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

LOWEST_UID = config.getint('posix', 'lowest_uid')
HIGHEST_UID = config.getint('posix', 'highest_uid')


def gen_storage_id(id):
    m = hashlib.md5()
    m.update(id)
    return LOWEST_UID + int(m.hexdigest(), 16) % HIGHEST_UID


def create_user_credentials(storage_type, storage_id, space_name, client_ip,
                            user_details):
    """Creates user credentials for POSIX storage based on provided user data.
    """
    user_id = user_details["id"]
    if user_id == "0":
        return PosixCredentials(0, 0)

    uid = gid = gen_storage_id(user_id)
    return PosixCredentials(uid, gid)
