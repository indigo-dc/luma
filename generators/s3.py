# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Example S3 credentials generator.
"""

import ConfigParser
import os

from luma.credentials import S3Credentials

config = ConfigParser.RawConfigParser()
config.read(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'generators.cfg'))

ACCESS_KEY = 'AccessKey'
SECRET_KEY = 'SecretKey'

if config.has_section('s3'):
    ACCESS_KEY = config.get('s3', 'access_key')
    SECRET_KEY = config.get('s3', 'secret_key')


def create_user_credentials(storage_type, storage_id, space_id, client_ip,
                            user_details):
    """Creates user credentials for S3 storage based on provided user data.
    """
    return S3Credentials(ACCESS_KEY, SECRET_KEY)
