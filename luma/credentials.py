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

    def __init__(self, uid, gid):
        Credentials.__init__(self)
        self.params['uid'] = str(uid)
        self.params['gid'] = str(gid)


class S3Credentials(Credentials):
    """Class representing users S3 storage credentials"""

    def __init__(self, access_key, secret_key):
        Credentials.__init__(self)
        self.params['accessKey'] = access_key
        self.params['secretKey'] = secret_key


class CephCredentials(Credentials):
    """Class representing users Ceph storage credentials"""

    def __init__(self, username, key):
        Credentials.__init__(self)
        self.params['username'] = username
        self.params['key'] = key


class SwiftCredentials(Credentials):
    """Class representing users Swift storage credentials"""

    def __init__(self, username, password):
        Credentials.__init__(self)
        self.params['username'] = username
        self.params['password'] = password
