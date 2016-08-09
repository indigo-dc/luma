# coding=utf-8
"""Author: Michal Wrona
Copyright (C) 2016 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Contains storage credentials representations.
"""


class Credentials:
    """Base class representing users storage credentials"""

    def __init__(self):
        self.params = {}

    def to_dict(self):
        return self.params


class PosixCredentials(Credentials):
    """Class representing users Posix storage credentials"""

    def __init__(self, uid, gid=None):
        Credentials.__init__(self)
        self.params['type'] = 'Posix'
        self.params['uid'] = uid
        if gid:
            self.params['gid'] = gid


class S3Credentials(Credentials):
    """Class representing users S3 storage credentials"""

    def __init__(self, access_key, secret_key):
        Credentials.__init__(self)
        self.params['type'] = 'S3'
        self.params['accessKey'] = access_key
        self.params['secretKey'] = secret_key


class CephCredentials(Credentials):
    """Class representing users Ceph storage credentials"""

    def __init__(self, user_name, user_key):
        Credentials.__init__(self)
        self.params['type'] = 'Ceph'
        self.params['userName'] = user_name
        self.params['userKey'] = user_key


class SwiftCredentials(Credentials):
    """Class representing users Swift storage credentials"""

    def __init__(self, user_name, password):
        Credentials.__init__(self)
        self.params['type'] = 'Swift'
        self.params['userName'] = user_name
        self.params['password'] = password
