import time
import random
import string
import unittest
import subprocess as sp

import requests


LUMA_IP = 'localhost'
LUMA_PORT = 8080
LUMA_API_PATH = 'api/v3/luma'
URL = 'http://{ip}:{port}/{api_path}'.format(ip=LUMA_IP, port=LUMA_PORT,
                                             api_path=LUMA_API_PATH)


USER_DETAILS_1 = {
    "id": "9743a66f914cc249efca164485a19c5c"
}

USER_DETAILS_2 = {
  "emailList": [
    "user.1@example2.com",
    "user.one@example2.com",
    "user.i@example2.com"
  ],
  "id": "9743a66f914cc249efca164485a19c5c",
  "connectedAccounts": [
    {
      "emailList": [
        "user.1@example.com",
        "user.one@example.com",
        "user.i@example.com"
      ],
      "idp": "github",
      "login": "user1",
      "name": "User One",
      "userId": "5c28904a-124a-4035-853c-36938143dd4e"
    },
    {
      "custom": {
        "eduPersonPrincipalName": "john@example.com",
        "userCertificateSubject": "/C=PL/O=GRID/O=ACME/CN=John Doe"
      },
      "emailList": [
        "user.1@egi.eu"
      ],
      "idp": "EGI",
      "login": "user1",
      "name": "User One",
      "userId": "john@example.com"
    }
  ],
  "login": "user.one",
  "name": "user1"
}

USER_DETAILS_3 = {
  "connectedAccounts": [ {
      "emailList": [
        "user.1@egi.eu"
      ],
      "idp": "EGI"
    }
  ],
}

USER_DETAILS_4 = {
  "connectedAccounts": [ {
      "emailList": [
        "user.2@egi.eu"
      ],
      "idp": "EGI"
    }
  ],
}

POSIX_STORAGE_CREDENTIALS = {
    "storageId": "1",
    "type": "posix",
    "aclName": "user@example.com",
    "uid": 1001,
    "gid": 1001
}

POSIX_STORAGE_CREDENTIALS_DIFFERENT_GROUP = {
    "storageId": "1",
    "type": "posix",
    "uid": 1001,
    "gid": 1005
}

POSIX_STORAGE_CREDENTIALS_STRINGS = {
    "uid": "1001",
    "type": "posix",
    "id": "1",
    "gid": "1005"
}

S3_STORAGE_CREDENTIALS = {
    "storageId": "2",
    "type": "s3",
    "accessKey": "ABCD",
    "secretKey": "1234"
}

CEPH_STORAGE_CREDENTIALS = {
    "storageId": "3",
    "type": "ceph",
    "key": "ABCD",
    "username": "user1"
}

GLUSTERFS_STORAGE_CREDENTIALS = {
    "storageName": "GlusterFS4",
    "storageId": "4",
    "type": "glusterfs",
    "uid": 1001,
    "gid": 1001
}

MULTI_STORAGE_CREDENTIALS = [
    POSIX_STORAGE_CREDENTIALS,
    S3_STORAGE_CREDENTIALS,
    CEPH_STORAGE_CREDENTIALS,
    GLUSTERFS_STORAGE_CREDENTIALS
]

GROUP_DETAILS = {
    "gid": 1001,
    "aclName": "users",
    "id": "1"
}

GROUP_DETAILS_USERS2 = {
    "gid": 1001,
    "aclName": "users2",
    "id": "1"
}

class TestLUMA(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.proc = sp.Popen(['python3', 'app.py'])
        # wait some time for app to start
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()

    def test_group_mapping(self):
        idp, group_id = random_string(10), random_string(20)
        path = '/admin/{idp}/groups/{gid}'.format(idp=idp, gid=group_id)
        url = URL + path

        # check if one can add group mapping
        r = requests.put(url, json=[GROUP_DETAILS])
        self.assertEqual(r.status_code, 204)

        # assert correct retrieve of data after correct insert
        r = requests.get(url)
        self.assertEqual(r.json(), [GROUP_DETAILS])

        # check group resolving
        group_details_complete = GROUP_DETAILS.copy()
        r = requests.post(URL + '/resolve_group', json=group_details_complete)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'idp': idp, 'groupId': group_id})

        # check if group without aclName field will be resolved
        group_details_without_acl = GROUP_DETAILS.copy()
        del group_details_without_acl['aclName']
        r = requests.post(URL + '/resolve_group', json=group_details_without_acl)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'idp': idp, 'groupId': group_id})

        # check group resolving based on acl
        r = requests.post(URL + '/resolve_acl_group', json=GROUP_DETAILS)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'idp': idp, 'groupId': group_id})

        # check group resolving returning 404 without correct aclName
        r = requests.post(URL + '/resolve_acl_group', json=GROUP_DETAILS_USERS2)
        self.assertEqual(r.status_code, 404)

        # delete mapping
        r = requests.delete(url)
        self.assertEqual(r.status_code, 204)

        # after delete mapping should not be available
        r = requests.get(url)
        self.assertEqual(r.status_code, 404)


    def test_user_mapping(self):
        # check if one can add users mapping
        r1 = requests.post(URL + '/admin/users', json=USER_DETAILS_1)
        self.assertEqual(r1.status_code, 201)
        _, lid = r1.headers['Location'].rsplit('/', 1)
        url = URL + '/admin/users/{lid}'.format(lid=lid)

        # assert correct retrieve of data after correct insert
        r2 = requests.get(url)
        self.assertEqual(r2.json(), normalize_user_details(USER_DETAILS_1.copy()))

        # assert userDetails can be updated
        r3 = requests.put(url, json=USER_DETAILS_2)
        self.assertEqual(r3.status_code, 204)
        r4 = requests.get(url)
        self.assertEqual(r4.json(), normalize_user_details(USER_DETAILS_2.copy()))

        # set user credentials for multiple storages
        r5 = requests.put(url + '/credentials', json=MULTI_STORAGE_CREDENTIALS)
        self.assertEqual(r5.status_code, 204)

        # check normal luma
        for credentials in MULTI_STORAGE_CREDENTIALS:
            storage_id = credentials.get('storageId')
            storage_name = credentials.get('storageName')
            user_id = USER_DETAILS_2['id']
            json = {'userDetails': {'id': user_id}}
            if storage_id != None:
                json['storageId'] = storage_id
            if storage_name != None:
                json['storageName'] = storage_name
            r6 = requests.post(URL + '/map_user_credentials', json=json)
            self.assertEqual(r6.status_code, 200)
            awaited_credentials = {key: val
                                   for key, val in credentials.items()
                                   if key not in ('storageId', 'storageName', 'type')}
            self.assertEqual(r6.json(), awaited_credentials)

        # check reverse luma
        for credentials in MULTI_STORAGE_CREDENTIALS:
            r7 = requests.post(URL + '/resolve_user', json=credentials)
            self.assertEqual(r7.status_code, 200)
            self.assertEqual(r7.json(), {'idp': 'onedata',
                                         'userId': USER_DETAILS_2['id']})

        # check reverse luma for file with different group than owner's default
        r7 = requests.post(URL + '/resolve_user', json=POSIX_STORAGE_CREDENTIALS_DIFFERENT_GROUP)
        self.assertEqual(r7.status_code, 200)
        self.assertEqual(r7.json(), {'idp': 'onedata',
                                     'userId': USER_DETAILS_2['id']})

        # check reverse luma for file with uid passed as string
        r7 = requests.post(URL + '/resolve_user', json=POSIX_STORAGE_CREDENTIALS_STRINGS)
        self.assertEqual(r7.status_code, 404)

        # check reverse luma based on ACl
        r7 = requests.post(URL + '/resolve_acl_user', json=POSIX_STORAGE_CREDENTIALS)
        self.assertEqual(r7.status_code, 200)
        self.assertEqual(r7.json(), {'idp': 'onedata',
                                     'userId': USER_DETAILS_2['id']})

        posix_storage_without_aclname = POSIX_STORAGE_CREDENTIALS
        del posix_storage_without_aclname['aclName']
        r7 = requests.post(URL + '/resolve_acl_user', json=posix_storage_without_aclname)
        self.assertEqual(r7.status_code, 404)

        # delete mapping
        r8 = requests.delete(url)
        self.assertEqual(r8.status_code, 204)

        # after delete mapping should not be available
        r9 = requests.get(url)
        self.assertEqual(r9.status_code, 404)

    def test_user_mapping_based_on_email(self):
        # check if one can add users mapping
        r1 = requests.post(URL + '/admin/users', json=USER_DETAILS_3)
        self.assertEqual(r1.status_code, 201)
        _, lid = r1.headers['Location'].rsplit('/', 1)
        url = URL + '/admin/users/{lid}'.format(lid=lid)

        # assert correct retrieve of data after correct insert
        r2 = requests.get(url)
        self.assertEqual(r2.json(), normalize_user_details(USER_DETAILS_3.copy()))

        # set user credentials for multiple storages
        r3 = requests.put(url + '/credentials', json=MULTI_STORAGE_CREDENTIALS)
        self.assertEqual(r3.status_code, 204)

        # check normal luma
        for credentials in MULTI_STORAGE_CREDENTIALS:
            storage_id = credentials.get('storageId')
            storage_name = credentials.get('storageName')
            json = {'userDetails': USER_DETAILS_3}
            if storage_id != None:
                json['storageId'] = storage_id
            if storage_name != None:
                json['storageName'] = storage_name
            r6 = requests.post(URL + '/map_user_credentials', json=json)
            self.assertEqual(r6.status_code, 200)
            awaited_credentials = {key: val
                                   for key, val in credentials.items()
                                   if key not in ('storageId', 'storageName', 'type')}
            self.assertEqual(r6.json(), awaited_credentials)

        # Check luma with invalid credentials
        for credentials in MULTI_STORAGE_CREDENTIALS:
            storage_id = credentials.get('storageId')
            storage_name = credentials.get('storageName')
            json = {'userDetails': USER_DETAILS_4}
            if storage_id != None:
                json['storageId'] = storage_id
            if storage_name != None:
                json['storageName'] = storage_name
            r6 = requests.post(URL + '/map_user_credentials', json=json)
            self.assertEqual(r6.status_code, 404)


def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(length))


def normalize_user_details(user_details):
    return user_details
